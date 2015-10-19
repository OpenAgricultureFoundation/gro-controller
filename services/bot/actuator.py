import time
import logging

from .element import Element


class Actuator(Element):
    """Actuator instance to be used in controls
    :type code: str
    :type index: int
    :type url: str
    :type sensing_point_list: []
    :type actuator_type_dict: dict
    :type _override: bool
    :type _override_endtime: float
    """
    type = 'actuator'

    _code_prefix = 'A'
    _max_state_settime = 10
    _update_interval = 1

    def __init__(self, bot, actuator_dict: dict):  #code: str, index: int, url: str, actuator_type_dict: dict, sys_state: State):
        """Create an Actuator instance.
        :param bot: Bot we are configuring this actuator for. Used to get other info (such as actuator_type code).
        :param actuator_dict: dict of data for this actuator
        """
        # Get code, index, url, etc
        # TODO we should be able to actually just get this info by following the relationships - shouldn't be that hard
        actuator_type_dict = bot.server.getJson(actuator_dict['actuator_type'], update=False)
        resource_dict = bot.server.getJson(actuator_dict['resource'], update=False)
        resource_type_dict = bot.server.getJson(resource_dict['resource_type'], update=False)
        resource_effect_dict = bot.server.getJson(actuator_type_dict['resource_effect'])
        control_profile_dict = bot.server.getJson(actuator_dict['control_profile'], update=False)
        self.code = self._code_prefix + resource_type_dict['code'] + resource_effect_dict['code']
        self.index = actuator_dict['index']
        self.url = actuator_dict['url']
        self.actuator_type_dict = actuator_type_dict
        self.sensing_point_list = []
        self.control_profile_dict = control_profile_dict
        self.effects_dictby_sensing_point_url = {}
        self.bot = bot
        # current_state is public so that we can update it from the actuator_handler in bot
        self.current_state = None   # keeps track of the state as reported by the groduino. used for retries (see state)

        # get the properties for this actuator. For each sensing point url, find the corresponding sensor and attached
        for property_url in actuator_type_dict['properties']:
            property_dict = bot.server.getJson(property_url, update=False)
            for url in property_dict['sensing_points']:
                try:
                    self.sensing_point_list.append(bot.getElementByUrl(url))
                except KeyError:
                    logging.warning('Actuator %s %d controls sensing point %s, but it isnt set up! likely inactive.',
                                    self.code, self.index, url)

        # get each effect, record it in effects_dictby
        for effects_dict in control_profile_dict['effects']:
            property_url = effects_dict['property']
            property_dict = bot.server.getJson(property_url, update=False)
            for sensing_point_url in property_dict['sensing_points']:
                try:    # If we have a sensing point for this url, add the corresponding effect dict to this actuator
                    self.bot.getElementByUrl(sensing_point_url)
                    self.effects_dictby_sensing_point_url[sensing_point_url] = effects_dict
                except KeyError:    # if we don't have this sensing point, don't add the effect!
                    logging.debug('No sensing point for %s. Not adding this effect to actuator %s %d',
                                  sensing_point_url, self.code, self.index)
                    continue

        # internal
        self._state = None          # used to keep track of state. access through the state property
        # TODO rename? having two states is confusing
        # NOTE: while override is set, self.state will NOT send any updates to the groduino
        self._override = False      # used to keep track of overrides. see override method.
        self._override_endtime = 0  # end time for override.
        self._state_settime = None  # used when updating state. if time-_state_settime > _max_state_settime: error
        self._last_updated = None   # used for retries, will only send a message once every _update_interval
        self._controlled_sensing_point = None     # record which sensing point the actuator is on for (ie why its on)

    def __str__(self):
        status = '(Actuator %s %d' % (self.code, self.index)
        if self.current_state is not None:
            status += ', cur. state %s' % self.current_state
        if self.state is not None:
            status += ' desired state %s' % self.state

        # Override will ignore _controlled_sensing_point
        if self._override:
            status += ' for OVERRIDE'
        elif self._controlled_sensing_point is not None:
            status += ' for %s %d' % (self._controlled_sensing_point.code, self._controlled_sensing_point.index)

        return status + ')'

    @property
    def value(self):
        """Since message handler will set value, this property just redirects to self.current_value.
        """
        return self.current_state

    @value.setter
    def value(self, value):
        self.current_state = value

    @property
    def state(self):
        """Set actuator state (actually sends to the groduino as well). Getter is normal, setter only sends on change.
        """
        return self._state

    # update does the actual sending so that we can do retries properly.
    @state.setter
    def state(self, value):
        if value != self._state and not self._override:   # Don't send anything if we are in override
            self._state = value
            logging.debug('actuator %s %d changing to state %f', self.code, self.index, value)
            self._state_settime = time.time()
            # done

            # self.bot.groduino.send('%s %d %f' % (self.code, self.index, value))

    # TODO could have a cleaner implementation of retries. queue of things to do or something?
    def update(self):
        """Update the actuator to state defined in self._state.

        self.current_state is current state of actuator as reported by groduino
        self.state is desired state based on what is set by controls or override (see self.state property)
        if the current state is not the desired state, we need to send something to the groduino.
            check if the are different. if they are
            check when the actuator was updated (curtime - self._last_updated, if it has been at all).
            if at least self._update_interval has passed:
            log the fact that we are updating, send the message.
            finally if we have been trying to update and more than self._max_state_settime has passed, log an error
        """
        if self.state is None or self.state == self.current_state:
            self._state_settime = None      # Set this to None so it doesn't look like we are behind later
            return

        # So the state is not None and they dont match:
        curtime = time.time()
        if self._last_updated is None or (curtime - self._last_updated > self._update_interval):
            if self._state_settime is None:     # If we dont have a set time yet (ex it was on during startup)
                self._state_settime = curtime   # set it to now so below code works
            logging.debug('updating %s %d, time %d settime %d', self.code, self.index, curtime, self._state_settime)

            self.bot.groduino.send('%s %d %f' % (self.code, self.index, self.state))
            self._last_updated = curtime

            if curtime - self._state_settime > self._max_state_settime:
                logging.error('actuator %s %d failed to change to state %s from %s',
                              self.code, self.index, self._state, self.current_state)
                self._state = None              # Unable to set actuator state, set state to None.
                # Note: state will get overwritten during control, so this won't stop it from sending...
                # if repeated sending after failure is a problem, we can set _last_updated time into the future

    # TODO document
    # TODO add output so we can see why things are switching
    def simpleControl(self):
        """Calculates desired state for this actuator based on self.effects_dictby...
        """

        # loop over effects.items()
        # we will add all the desired states to this dict
        desired_states_dictby_value = {}
        for sensing_point_url, effects_dict in self.effects_dictby_sensing_point_url.items():
            e = effects_dict        # just shortening to make the code below decent
            if e['effect_on_active'] == 0:      # No point in turning it on if it doesn't do anything
                continue
            # try:
            sensing_point = self.bot.getElementByUrl(sensing_point_url)
            # except KeyError:
            #     continue        # TODO super hack because is_active doesn't work
            #     # This should be fine, but we should log when we can't find the sensing point... logging from here
            #     # would result in way too much spam (this is called a lot!)
            #     # ACTUALLY nevermind, we shouldn't store effects dict for urls that aren't active
            #     # fixed above, commenting out and testing this
            current_value = sensing_point.value
            desired_value = sensing_point.desired_value
            if desired_value is None or current_value is None:
                continue

            delta = desired_value - current_value

            # Implements basic band, if below thres, actuate until within thres/2
            if (abs(delta) < e['threshold']) and (self.state == 0):      # if the magnitude of error is less than the threshold, do nothing
                # we don't even need to add it to the desired states since its 0
                continue
            elif (abs(delta) < e['threshold']/4) and (self.state != 0):
                continue
            elif delta*e['effect_on_active'] < 0:  # ex. want to heat (pos delta) and effect is negative: do nothing
                continue
            elif self.actuator_type_dict['is_binary']:  # if its binary, we know we need to turn it on if we got here
                # if we have more than one with the same value, it will overwrite, but thats OK. we only care about max
                desired_states_dictby_value[1] = (sensing_point.code, sensing_point.index)
                continue
            else:
                desired_state = delta/(e['operating_range_max']-e['operating_range_min'])
                desired_states_dictby_value[desired_state] = (sensing_point.code, sensing_point.index)

        # Figure out what the state should be!
        if len(desired_states_dictby_value) == 0:       # If we don't have any thing in the dict, set to 0
            self._controlled_sensing_point = None
            self.state = 0
            return

        # Get all the values, find the max, set the actuator to that, and record what sensing point this is for
        values = desired_states_dictby_value.keys()
        max_val = max(values)

        self.state = max_val
        sensing_point_code, sensing_point_index = desired_states_dictby_value[max_val]
        self._controlled_sensing_point = self.bot.getElementByCodeIndex('sensing_point',
                                                                        sensing_point_code, sensing_point_index)
        logging.debug('ACT: setting act %s %d to %f for pt %s %d', self.code, self.index, max_val,
                      sensing_point_code, sensing_point_index)


    def sensingPointValues(self):
        """returns the sensing point values for this actuator"""
        return [sensing_point.value for sensing_point in self.sensing_point_list]

    # TODO use timer with callback to clear override. For now, depends on self.state being set through polling
    # or use a queue in bot
    def override(self, value): #, endtime):
        """Override the state on the actuator until endtime
        :param value: value to override to
        :param endtime: time to override til as unix timestamp
        """
        #if endtime > time.time():  # if endtime hasn't passed yet
        self._override = False  # just in case we were already in override
        self.state = value
        self._override = True
        #self._override_endtime = endtime
