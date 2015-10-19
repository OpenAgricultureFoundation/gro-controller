from collections import deque
import logging
import time
import requests         # TODO should just have everything go through server

import sys
if sys.version_info < (3, 3, 0):
    from requests import ConnectionError

from .element import Element


# TODO should we be using resource property instead of sensing point for most of this stuff?
class SensingPoint(Element):
    """Use sensingPoint.value to read/write latest value
    :type code: str
    :type index: int
    :type post_url: str
    :type threshold: float
    :type _timestamp: float
    :type _last_value: float
    :type _posted: bool
    :type _desired_value: float
    :type _desired_value_updated: bool
    """
    type = 'sensing_point'

    code_prefix = 'S'       # TODO use this for message handling too or note that we have to write it elsewhere?
    post_suffix = '/value/'
    threshold = 5.0         # we will get a warning in sensor hasn't been updated in threshold seconds

    def __init__(self, bot, sensing_point_dict: dict):
        """Create a SensingPoint instance
        :param bot: Bot we are configuring this sensor for. Used to get other info (such as resource property code).
        :param sensing_point_dict: dict of data for this sensing point.
        """
        # Get the code, index, url, post_url
        resource_property = bot.server.getJson(sensing_point_dict['property'], update=False)
        resource_type = bot.server.getJson(resource_property['resource_type'], update=False)

        # public attributes
        self.code = self.code_prefix + resource_type['code'] + resource_property['code']
        self.index = sensing_point_dict['index']
        self.url = sensing_point_dict['url']
        self.post_url = self.url + self.post_suffix
        self.is_active = sensing_point_dict['is_active']

        # internal
        self._timestamp = None       # timestamp of last sample ex 1438646393.9064195
        self._last_value = None      # most recent reading
        self._posted = True          # indicates whether last_value has been written to the server so we don't repeat
        self._desired_value = None   # desired set point
        self._desired_value_updated = False  # so that we can easily find set points that have changed

        # buffer of (timestamp, value) to write if we want multiple values per post request
        # length limited so that we don't waste too much memory, old values will get thrown away on overflow
        self._values_buffer = deque(maxlen=50)

    def __str__(self):
        status = '(SensingPoint %s %d' % (self.code, self.index)
        if self.value is not None and self._timestamp is not None:
            status += ', latest %.2f @ %d' % (self.value, self._timestamp)
        if self.desired_value is not None:
            status += '. Desired %.2f' % self.desired_value
        return status + ')'

    @property
    def value(self):
        """Get the latest sensor value. when writing values, will
        """
        return self._last_value

    @value.setter
    def value(self, value):
        current_time = time.time()
        # Update if new value or hasn't been updated for a while
        if (self._last_value != value) or (current_time - self._timestamp > 60): # TODO shouldn't be hardcoded 
            self._last_value = value
            self._timestamp = current_time
            self._posted = False  # TODO is this only for _last_value? update docs/methods below!

            # If the last timestamp was more than 5 seconds ago, record this value
            if len(self._values_buffer) == 0 or current_time - self._values_buffer[-1][0] >= 5:
                self._values_buffer.append((current_time, value))  # append adds to the right

            if len(self._values_buffer) > 20:  # TODO shouldn't be hardcoded
                logging.warn('Buffer is getting big (%d) for %s', len(self._values_buffer), str(self))

    @property
    def desired_value(self):
        """desired_value. get is normal, setter also sets self.desired_value_update=True
        """
        return self._desired_value

    @desired_value.setter
    def desired_value(self, value):
        self._desired_value = value
        self._desired_value_updated = True

    @property
    def formatted_values_list(self):
        """list of values formatted for server (will have timestamp, value, origin). write None to here to clear buffer
        """
        values_list = []
        for timestamp, value in self._values_buffer:
            value_dict = {"timestamp": int(timestamp),
                          "value": value,
                          "sensing_point": self.url}
            values_list.append(value_dict)
        return values_list

    @formatted_values_list.setter
    def formatted_values_list(self, value):
        if value is None:
            self._values_buffer.clear()
        else:   # should only ever be writing None, everything else is invalid
            raise ValueError

    # TODO do we still need this? Should bot or server just manage all data being passed?
    def postLastValue(self):
        """Post lastValue for this sensor to the server. Raise ConnectionError on failure
        NOTE: this clears the internal value buffer, recommend using either postLastValue or postNewValues, not both.
        """
        if self._posted:
            logging.debug("last value for %s %d already posted!", self.code, self.index)
            return

        post_data = {
            "timestamp": self._timestamp,
            "value": self._last_value,
        }
        req = requests.post(self.post_url, json=post_data)
        if req.status_code != 200:
            logging.error('Failed to send data for %s %d. '
                          'Aborting, not setting self._posted. Safe to retry.', self.code, self.index)
            raise ConnectionError
        self._posted = True
        self._values_buffer.clear()

    def postNewValues(self):
        """Post all new values for this sensor to the server. Raise ConnectionError on failure
        """
        # TODO get rid of this function or make it use the formattedValuesList to speed things up
        if len(self._values_buffer) == 0:
            logging.debug('No new values for %s %d', self.code, self.index)
            return

        assert type(self._values_buffer[0]) == tuple
        for (timestamp, value) in self._values_buffer:
            post_data = {
                "timestamp": timestamp,
                "value": value,
            }
            req = requests.post(self.post_url, json=post_data)
            if req.status_code == 200:
                logging.error('Failed to send data for %s %d. '
                              'Aborting, not clearing buffer.', self.code, self.index)
                raise ConnectionError
        self._values_buffer.clear()

    @classmethod
    def mainMessageHandler(cls, bot, code_index_str, message):
        """Finds the appropriate sensing point and calls individualMessageHandler on it

        Overwrites the base class version to add check inactive_sensing_points before handling message
        :param bot: Bot instance this request is coming from
        :param code_index_str: ex 'SATM 1'
        :param message: ex 22.8, but could also be 'ERROR' or something.
            Shouldn't have to worry about the message, just pass it to the individual sensing point
        """
        # Check if this is an inactive sensor
        if code_index_str in bot.inactive_sensing_points_dictby_codeindexstr:     # If inactive, skip
            if code_index_str not in bot.invalid_message_codeindex_list:          # Used to log once, see def in bot
                logging.warning('Got message for %s, but it is inactive. Ignoring from now on', code_index_str)
                bot.invalid_message_codeindex_list.append(code_index_str)
            return

        super().mainMessageHandler(bot, code_index_str, message)
