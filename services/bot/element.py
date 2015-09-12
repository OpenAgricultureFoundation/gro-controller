import logging
import time

class Element:
    """Base class for Actuator, SensingPoint, etc

    See Actuator or SensingPoint for an example of how to override
    """
    type = 'element'        # override this, ex type = 'actuator'

    def __init__(self):        # Should override this in subclass without calling it
        self.code = 'ELEM'
        self.index = 0

    # ----- Message Handling -----
    _error_max_retries = 5     # If we get an error with the sensors, retry this many times
    _error_period = 60         # if we retry more than the max in this period,
    _error_timeout = 600       # then wait this long. (so we don't spam the log)
    _error_retry_count = 0     # keep track of how many times we retried
    _error_period_start = 0    # and when the error period started

    @classmethod
    def mainMessageHandler(cls, bot, code_index_str, message):
        """Finds the appropriate element and calls individualMessageHandler on it
        :param bot: Bot instance this request is coming from
        :param code_index_str: ex 'SATM 1'
        :param message: ex 22.8, but could also be 'ERROR' or something.
            Shouldn't have to worry about the message, just pass it to the individual element
        """
        # If we know this is an invalid code_index_str, ignore it
        if code_index_str in bot.invalid_message_codeindex_list:
            return

        # Get the code, index for this element
        code, index_str = code_index_str.split()
        index = int(index_str)
        # logging.debug("code %s index %d, message %s", code, index, message)  # too much printing!

        # Try to find the element, else error
        try:
            element_inst = bot.getElementByCodeIndex(element_type=cls.type, code=code, index=index)
        except KeyError:
            logging.error("Got %s %s, but can't find element for it! Ignoring from now on", code_index_str, message)
            bot.invalid_message_codeindex_list.append(code_index_str)
            return

        # We don't have a need for the return value yet, but can use it to tell if handling succeeded
        element_inst.callHandlerWithRetries(element_inst.individualMessageHandler, message)

    def callHandlerWithRetries(self, message_handler_fn, *args, **kwargs):
        """Calls the supplied message_handler_fn with any supplied arguments if it doesn't raise too many exceptions

        Uses self._error_max_retries, self._error_period, self._error_timeout,
        self._error_retry_count, self._error_period_start.
        :param message_handler_fn: message handler function to call.
        """
        curtime = time.time()

        # If we had too many errors, wait until (the end of the period + the timeout)
        if self._error_retry_count >= self._error_max_retries and \
           curtime < (self._error_period_start + self._error_period + self._error_timeout):
            return False

        # otherwise we have not had too many errors, everything is ok
        # check if the error period has ended. If so reset count
        if curtime > (self._error_period_start + self._error_period):
            self._error_period_start = curtime
            self._error_retry_count = 0

        try:
            message_handler_fn(*args, **kwargs)
        except Exception:       # TODO figure out how to log the actual message (all of *args, **kwargs preferably)
            logging.exception("%s %d failed to handle message.", self.code, self.index)
            self._error_retry_count += 1
            if self._error_retry_count >= self._error_max_retries:
                logging.error('Got %d errors for %s %s %d in %f. Will stop handling messages for %d',
                              self._error_retry_count, self.type, self.code, self.index,
                              self._error_period, self._error_timeout)

    def individualMessageHandler(self, message) -> bool:
        """Handle a message for this element specifically.

        This method should log errors but shouldn't need to implement retries - mainMessageHandler takes care of that
        :param message: ex 22.8, but could also be 'ERROR' or something
        :return: True/False to indicate if the message was handled
        """
        self.value = float(message)

