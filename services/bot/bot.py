# This file holds all of the code related to the physical bot, including sensors, actuators, etc.
# It uses Server to get updates

import logging
import requests  # TODO all server stuff should be through server
import json      # TODO shouldn't need this
import time
import os

from ..server import Server, ServerResourceLazyDict
from ..configuration import ManualProfiler

from .actuator import Actuator
from .sensingPoint import SensingPoint

#SERVER = ''         # TODO

# TODO be able to add actuators/sensing points dynamically
# TODO be consistent with suffixes (ex groduino_inst)
class Bot:
    status_file_name = 'grostatus.log'

    # TODO document
    def __init__(self, groduino_inst, server_inst: Server):
        """Set up the bot. Get the necessary info from the server, etc
        :return:
        """

        self.server = server_inst
        self.groduino = groduino_inst
        self.server_update_period = 15       # Update from/to the server this often
        self.invalid_message_codeindex_list = []        # TODO document
        self.inactive_sensing_points_dictby_codeindexstr = {}  # Used to store dict of inactive sensors instances

        # TODO do we want even more dynamic? Can parse the API ROOT, get all available properties, get if referenced
        # TODO having server info by url would make things a lot easier... should we just store it in server?
        self.server_info = {}  # NOTE the values in this array usually aren't updated! Call updateFromServer if needed!
        for endpoint_name in ['resource_type', 'resource_property', 'actuator', 'actuator_type', 'sensing_point',
                              'control_profile']:
            self.server_info[endpoint_name] = ServerResourceLazyDict(endpoint_name, self.server)

        # INTERNAL
        self._run_profiler = ManualProfiler()
        self._last_server_update_time = 0       # For run, only want to update server every self.server_update_period
        self._status_last_logged = time.time()  # We don't want to log on the first run, so set to current time
        self._unposted_message_count = 0
        self._element_dictby_url = {}           # ex _element_dictby_url['http.../actuator/1/']
        self._element_dictby_code_index = {'sensing_point': {},
                                           'actuator': {},
                                           }        # ex _element_dictby_code_index['sensing_point']['SAHU'][1]

        # TODO this is pretty sloppy below, maybe a separate class
        self._run_stats_dict = {'run_times': {}, }           # For profiling the bot.run loop. look there for more info
        self._run_enum_dict = {'status': 1, 'server': 2}

        # TODO document better. Prolly rename too.
        self._message_handlers_dictby_code = {'S': SensingPoint.mainMessageHandler,
                                              'A': Actuator.mainMessageHandler,
                                              'G': Bot.generalMessageHandler,
                                              }      # These will handle the messages from the groduino based on msg[0]

        # INIT
        # Set up sensing points, actuators, and all that good stuff
        self._populateSensingPoints()
        self._populateActuators()

    # ----- INIT and creation -----

    def _populateSensingPoints(self):
        """Populate the sensing points from server_info['sensing_point']

        We add create an instance for each sensing point, even if it isn't active
        BUT we don't add them all to the same list, see addSensingPoint
        This will make it easier to change to dynamic later - just change which list the instance is in
        """

        for sensing_point_dict in self.server_info['sensing_point'].values():
            sensing_point_inst = SensingPoint(self, sensing_point_dict)
            self.addSensingPoint(sensing_point_inst)

    # TODO can actuator be dynamic enough to work without sensing points populated?
    # would need to have that queue of methods on bot and update sensing point later
    def _populateActuators(self):
        for actuator_dict in self.server_info['actuator'].values():
            actuator_inst = Actuator(self, actuator_dict)
            self.addActuator(actuator_inst)

    def addActuator(self, actuator_inst: Actuator):
        """Add an actuator to the bot and store it in the proper places

        Actuator is linked to sensing points, it will throw KeyError if linked sens. pts. are not present
        :param actuator_inst: an instance of Actuator
        """
        a = actuator_inst
        self._element_dictby_url[a.url] = a
        if a.code not in self._element_dictby_code_index['actuator']:
            self._element_dictby_code_index['actuator'][a.code] = {}
        self._element_dictby_code_index['actuator'][a.code][a.index] = a

    def addSensingPoint(self, sensing_point_inst: SensingPoint):
        """Add an sensor to the bot and store it in the proper places

        If the sensing point isn't active, don't add to the elements dict, add to the inactive list
        :param sensing_point_inst: an instance of Sensor
        """
        s = sensing_point_inst
        if not s.is_active:     # If inactive, add to inactive list but don't add to the element_dictby dicts
            self.inactive_sensing_points_dictby_codeindexstr[s.code + ' ' + str(s.index)] = s
            return
        self._element_dictby_url[s.url] = s
        if s.code not in self._element_dictby_code_index['sensing_point']:
            self._element_dictby_code_index['sensing_point'][s.code] = {}
        self._element_dictby_code_index['sensing_point'][s.code][s.index] = s

    # ----- Getting elements and the like -----

    # TODO should None be ellipsis? see https://docs.python.org/dev/library/typing.html and PEP 484
    # TODO should we have a faster way to return all elements for a certain type? maybe concat the dicts?
    # OR A GENERATOR! just return one element at a time
    def getElementByCodeIndex(self, element_type: str, code: str=None, index: int=None):
        """Utility method so that we don't have to write the same code for getActuator/Sensor ByCodeIndex

        Gets the element for a specified code and index.
        If code=None, return all elements of this type as flat list of instances (not [code][index])
        If index=None and code!=None, returns dict of all elements for this code
        raises KeyError if the element isn't found
        :param element_type: 'actuator' or 'sensing_point'
        :param code: ex 'SAHU'
        :param index: ex 1
        :return: Actuator or SensingPoint instance or dict of instances by index
        """
        # We are returning this as a list. If you wanted them as a dict you could just the internal dict...
        if code is None:        # Don't care what index is, return all
            l = []
            for index_dict in self._element_dictby_code_index[element_type].values():
                for inst in index_dict.values():
                    l.append(inst)
            return l

        if index is None:
            return self._element_dictby_code_index[element_type][code]

        # If we got here, must have both.
        return self._element_dictby_code_index[element_type][code][index]

    def getElementByUrl(self, url: str):
        """Get the element for a given URL.

        raises KeyError if the element isn't found
        :param url: url of the element we want to get, ex 'http://.../actuator/23/'
        :return: Actuator or SensingPoint instance.
        """
        return self._element_dictby_url[url]

    # ----- Running -----
    # TODO this could be moved to a state machine implementation to make things cleaner/better
    def run(self):
        """Run the bot (forever)! Get data from the server, update the bot, run controls, post data!
        """

        # Want to add profiling to this function. It will look pretty ugly...
        clear_run_stats_flag = 0
        while 1:
            # Set up for profiling
            self._run_profiler.startLoop()

            # Try to get a message from the groduino
            buffer_cleared = self.updateFromGroduino()
            self._run_profiler.addPoint('updateFromGroduino done')

            self.updateActuators()
            self._run_profiler.addPoint('updateActuators done')

            # Update the status file
            # TODO this shouldn't happen same run we are posting to server. Or the one right after.
            if time.time() - self._status_last_logged > 10:
                self._run_profiler.addPoint('starting status routine')

                status_str = '\n'.join(self.getStatusList())
                self._run_profiler.addPoint('got status, logging')

                self._status_last_logged = time.time()
                logging.info(status_str)
                self._run_profiler.addPoint('logged status, writing')

                # This will overwrite status each time, just watch the file
                with open(self.status_file_name, 'w') as f:
                    f.write(status_str)
                clear_run_stats_flag += 1       # this way we can do it every x runs below
                self._run_profiler.addPoint('done writing, done status')

            # we want to update whenever we clear the buffer OR every 5 seconds, whichever is sooner
            curtime = time.time()
            if self._last_server_update_time != 0 and \
                    (curtime - self._last_server_update_time > self.server_update_period):
                logging.warn("Didn't clear serial buffer within update period %d", self.server_update_period)

            # TODO just clear the serial buffer. better to be up to date than get every message
            if (buffer_cleared and self._unposted_message_count > 0) or \
                    curtime - self._last_server_update_time > self.server_update_period:
                self._run_profiler.addPoint('starting post routine')

                self._unposted_message_count = 0
                self._last_server_update_time = time.time()
                self.getOverrides()
                self._run_profiler.addPoint('got overrides')

                self.getSetPointsFromServer()
                self._run_profiler.addPoint('got setpoints, posting data')

                self.postData()
                self._run_profiler.addPoint('done posting data')

                self.updateFromGroduino(blocking=True)      # Since we just posted, try to wait for a message

            if clear_run_stats_flag > 10:       # so we will still update, but it will aggregate for 10 batches
                clear_run_stats_flag = 0
                self._run_profiler.clear()
            self._run_profiler.endLoop()

    # TODO have a test message here, possibly through another variable
    def updateFromGroduino(self, blocking=False):
        """Get a message from the groduino (if available), parse the values to update the relevant info
        :return: bool indicating whether the buffer was clear
        """
        # TODO move the json parsing to groduino
        # TODO add a debug variable, if debugging get rid of all groduino operations
        message = self.groduino.receive(blocking=blocking)
        if not message:     # return True to indicate the buffer is clear
            return True     # TODO should we do something here?
        logging.debug('Handling: %s', message)      # TODO worry about timezones and stuff..

        try:        # Try to parse the message as json.
            message_dict = json.loads(message)
        except ValueError:
            logging.error('Unable to parse message, json.loads failed')
            logging.debug('', exc_info=True)
            return False

        self._unposted_message_count += 1           # If we got here, everything is ok, increment message count
        # Split the message_dict into key/value pairs.
        # key is code with index (ex SAHU 2). value is usually single float, can be list/dict (see groduino docs)
        for key, data in message_dict.items():
            try:
                self._message_handlers_dictby_code[key[0]](self, key, data)

            # NotImplemented - handler not written. ValueError - bad value. KeyError - no handler
            except (NotImplementedError, ValueError, KeyError):
                logging.error("Couldn't handle part of the message... I CAN'T HANDLE IT MAN!")
                logging.error("message part: %s %s", key, data)
                logging.debug('', exc_info=True)
                continue
            except:
                logging.exception("Couldn't handle %s %s", key, data)
                raise

    def updateActuators(self):
        """Updates any actuators that have not yet succeeded. Also does controls stuff
        """
        for actuator_inst in self.getElementByCodeIndex('actuator'):
            assert isinstance(actuator_inst, Actuator)
            actuator_inst.simpleControl()
            actuator_inst.update()

    def getSetPointsFromServer(self):       # seems like it works, can't test because of new format
        """Get all the setpoints and set them on the correct sensing points
        """
        # Get Server IP - this is horrible, omg...
        f = open(os.path.join('/home/pi/', 'server_ip.txt'), 'r')
        server_ip = f.readline();
        f.close()
        SERVER = "http://" + server_ip.strip() + "/"
        
        SERVER_SET_POINT = SERVER + 'tray/1/set_points/'            # TODO should be getting enclosure (only one)
        setpoint_list = self.server.getJson(SERVER_SET_POINT)     # NOTE Set point list is formatted differently! See db

        for code, value in setpoint_list.items():
            try:
                sensing_point_dict = self.getElementByCodeIndex('sensing_point', code='S' + code)
            except KeyError:        # If the sensinpoint is disabled but we still have a set point, ignore it
                if value is not None:       # If we got a None for an inactive sensor, thats ok
                    logging.warning('Got set point for %s, but theres no sensing point (probably inactive) ', code)
                continue

            for sensing_point_inst in sensing_point_dict.values():
                sensing_point_inst.desired_value = value

    def getOverrides(self):
        """Get all the overrides and set them on the correct actuator
        """
        cur_time = time.time()
        
        # Get Server IP - this is horrible, omg...
        f = open(os.path.join('/home/pi/', 'server_ip.txt'), 'r')
        server_ip = f.readline();
        f.close()
        SERVER = "http://" + server_ip.strip() + "/"

        SERVER_ACTUATOR = SERVER + 'actuator/'          # TODO no hardcode!
        actuator_list = self.server.getJson(SERVER_ACTUATOR)

        for actuator_dict in actuator_list:
            actuator_inst = self.getElementByUrl(actuator_dict['url'])
            assert isinstance(actuator_inst, Actuator)
            if actuator_dict['override_value'] is not None: #and actuator_dict['override_timeout'] > cur_time:
                logging.debug('%s overriden to state %f', str(actuator_inst), actuator_dict['override_value'])
                # actuator_inst.override(actuator_dict['override_value'], actuator_dict['override_timeout'])
                actuator_inst.override(actuator_dict['override_value'])
            else:
                actuator_inst._override = False      # TODO shouldn't be accessing private method. see override notes

    def postData(self):
        """Post data to the server. Uses the post method on each of the sens. pts. Raise ConnectionError on failure
        """
        # Get the formatted list from every sensor, combine, send
        formatted_values_list = []
        for sensing_point in self.getElementByCodeIndex('sensing_point'):
            assert isinstance(sensing_point, SensingPoint)
            formatted_values_list += sensing_point.formatted_values_list
            sensing_point.formatted_values_list = None      # To clear the sensing_point buffer

        self.server.postDataPoints(formatted_values_list)

    # ----- Status -----

    def getStatusList(self):
        status_list = ['-----STATUS-----']
        status_list += self.getActuatorStatusList()
        status_list += self.getSensingStatusList()
        status_list += self._run_profiler.getStatusList()
        status_list.append('-----END-----')
        return status_list

    def getActuatorStatusList(self):
        actuator_status_list = ['Actuator status:'] + \
                               ['\t'+str(x) for x in self.getElementByCodeIndex('actuator')]
        return actuator_status_list

    def getSensingStatusList(self):
        """Returns status of each sensing point as a list. Includes control info.
        :return: list of status. First is 'Sensing point status:' followed by each status indented by one tab
        """
        # for sensing_point_inst in self._element_dictby_url['sensing_point']:

        sensing_point_status_list = ['Sensing point status:'] + \
                                    ['\t'+str(x) for x in self.getElementByCodeIndex('sensing_point')]
        return sensing_point_status_list

    # ----- Misc -----

    # TODO should this be a separate class? or where should this be? prolly not inside the Bot class, maybe outside
    # TODO finish the handlers
    # this is for 'G' messages
    def generalMessageHandler(self, code_index_str, value):
        if code_index_str == 'GEND':
            return
        else:
            # raise NotImplementedError
            return      # TODO should be raising the error, but don't want that much spam right now


