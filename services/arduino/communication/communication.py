import time
import logging
import serial
import re

import sys
if sys.version_info < (3, 3, 0):
    from requests import ConnectionError


class Crc8(object):
    TABLE = [
        0, 94, 188, 226, 97, 63, 221, 131, 194, 156, 126, 32, 163, 253, 31, 65,
        157, 195, 33, 127, 252, 162, 64, 30, 95, 1, 227, 189, 62, 96, 130, 220,
        35, 125, 159, 193, 66, 28, 254, 160, 225, 191, 93, 3, 128, 222, 60, 98,
        190, 224, 2, 92, 223, 129, 99, 61, 124, 34, 192, 158, 29, 67, 161, 255,
        70, 24, 250, 164, 39, 121, 155, 197, 132, 218, 56, 102, 229, 187, 89, 7,
        219, 133, 103, 57, 186, 228, 6, 88, 25, 71, 165, 251, 120, 38, 196, 154,
        101, 59, 217, 135, 4, 90, 184, 230, 167, 249, 27, 69, 198, 152, 122, 36,
        248, 166, 68, 26, 153, 199, 37, 123, 58, 100, 134, 216, 91, 5, 231, 185,
        140, 210, 48, 110, 237, 179, 81, 15, 78, 16, 242, 172, 47, 113, 147, 205,
        17, 79, 173, 243, 112, 46, 204, 146, 211, 141, 111, 49, 178, 236, 14, 80,
        175, 241, 19, 77, 206, 144, 114, 44, 109, 51, 209, 143, 12, 82, 176, 238,
        50, 108, 142, 208, 83, 13, 239, 177, 240, 174, 76, 18, 145, 207, 45, 115,
        202, 148, 118, 40, 171, 245, 23, 73, 8, 86, 180, 234, 105, 55, 213, 139,
        87, 9, 235, 181, 54, 104, 138, 212, 149, 203, 41, 119, 244, 170, 72, 22,
        233, 183, 85, 11, 136, 214, 52, 106, 43, 117, 151, 201, 74, 20, 246, 168,
        116, 42, 200, 150, 21, 75, 169, 247, 182, 232, 10, 84, 215, 137, 107, 53
    ]

    def __init__(self, sum_=0x00):
        self.sum = sum_

    def _update(self, b):
            self.sum = self.TABLE[self.sum ^ b]

    def digest(self, st):
        self.sum = 0
        for ch in st:
            self._update(ord(ch))
        return self.sum


class Groduino:
    # ASCII Controls
    _kStartOfHeaderByte = 1
    _kStartOfTextByte = 2
    _kEndOfTextByte = 3
    _kEndOfTransmissionByte = 4
    _kEnquireByte = b'\x05'
    _kAcknowledgeByte = b'\x06'

    _MESSAGEBUFFER_SIZE = 8192
    _MESSAGEBUFFER_CUT_SIZE = 4096

    def __init__(self, port, serial_parameters):
        """
        :param port: port name (string) to open, ex '/dev/ttyACM0'
        :param serial_parameters: instance of configuration.SerialParameters
        :return: groduino instance that can Send/Receive, etc
        """
        self._message_buffer = ''

        self.ser = serial.Serial(port, baudrate=serial_parameters.baud_rate,
                                 timeout=serial_parameters.serial_read_timeout)
        self.establish_timeout = serial_parameters.establish_connection_timeout
        self.timeout = serial_parameters.receive_message_timeout
        self._reciprocateNewConnection()

    def close(self):
        """End the serial connection
        """
        self.ser.close()

    def send(self, message):
        """Send a message to the groduino. Will wrap it in proper start/end symbols
        :param message: message to send, no start or end symbols. ex message='ALP 1 1'
        :return:
        """

        logging.info("Sending: " + message)
        packed_message = chr(1)     # start of header
        packed_message += str(len(message))
        packed_message += chr(2)    # start of text
        packed_message += message
        packed_message += chr(3)    # end of text
        crc8 = Crc8()
        packed_message += str(crc8.digest(message))
        packed_message += chr(4)    # end of transmission
        self.ser.write(bytes(packed_message, 'UTF-8'))

    def receive(self, blocking=False):
        """ Gets a message from the groduino and returns it if available, else None.
        :return: single json string with all current sensor values (clean, no begin/end symbols). No trailing comma
        None if no message available
        """
        # Acquire New Messages
        incoming_message = self._acquireNewTransmission()
        while blocking and incoming_message is None:        # Block until we get a message, valid or not
            incoming_message = self._acquireNewTransmission()

        if incoming_message is None:
            logging.debug('No new message!')                # TODO too much spam
            return None
        # logging.debug('Received: %s', incoming_message)   # Should be logged higher up anyways

        try:
            # get:     header between \x01 and \x02     message    footer between \x03 and \x04
            # header and footer should be decimal only
            reggie = re.search(r"^\x01([0-9]*)\x02(.*)\x03([0-9]*)\x04$", incoming_message)
            message_length, clean_message, crc_received = reggie.groups()
            message_length = int(message_length)
            crc_received = int(crc_received)
            assert len(clean_message) == message_length
            if crc_received == 256:
                raise ConnectionError
            self._compareChecksums(crc_received, clean_message)
            clean_message = clean_message.strip(',')
            return clean_message

        # AttributeError->failed search, ValueError->not enough groups or int('string')
        # AssertionError->(obvious), ConnectionError->checksum
        except (AttributeError, ValueError, AssertionError, ConnectionError):
            logging.error("Received invalid message, discarding: %s:", incoming_message)
            logging.debug('', exc_info=True)
            return None

    # Function Definitions
    def _reciprocateNewConnection(self):
        """Sends/receives enquire and acknowledge for handshake with arduino. will raise ConnectionError on failure
        """
        start_time = time.time()
        logging.info("Establishing new connection")

        while True:
            if time.time() - start_time > self.establish_timeout:
                logging.error("Timed out waiting for enquire")
                raise ConnectionError

            incoming_char = self.ser.read()
            if incoming_char != b'':
                if incoming_char == self._kEnquireByte:     # Wait til we get enquire, send ack, wait for ack
                    logging.info("Received enquiry")
                    logging.info("Sending acknowledge")
                    self.ser.write(self._kAcknowledgeByte)
                    logging.info("Awaiting acknowledge")
                    while True:
                        if time.time() - start_time > self.establish_timeout:
                            logging.error("Timed out waiting for acknowledge")
                            raise ConnectionError

                        incoming_char = self.ser.read()
                        if incoming_char != "":
                            if incoming_char == self._kAcknowledgeByte:
                                logging.info("Received acknowledgement")
                                logging.info("Success in %f sec", time.time() - start_time)
                                return

    def _acquireNewTransmission(self):
        """Get a new (unchecked) message from the groduino (low-level).

        This function does a little bit of magic by using self._message_buffer.
        First it checks how many bytes are available in the buffer. If > 3.5k, it (neatly) flushes and logs overflow.
        We also check if _message_buffer is too big and flush
            So when we flush we may or may not get a complete message
        Then it appends all available bytes to the buffer
        Then it checks if there is a complete message in the buffer. If so, it sends it.
            It looks for a complete message ONLY by the endOfTransmission char. So if we have a bunch of crap,
            it will just get all of it until the next endOfTransmission. It will be filtered by the next level up,
            which verifies structure and checksum. This prevents hanging - it will just wait until the next end

        Note: this now blocks after flushing the buffer until we can get a complete message
        This is better since we don't want to post right after flushing the buffer, serial is more important
        :return: on success: a string that ends with endOfTransmission. on failure: None
        """

        # TODO Should store the last time we got a message so we can reset connection if it dies
        bytes_available_int = self.ser.inWaiting()
        # logging.debug('bytes: %d', bytes_available_int)
        # even if bytes_available is 0, we should check if we have any messages from before

        # First check if _message_buffer is too big. If so, chop it
        if len(self._message_buffer) > self._MESSAGEBUFFER_SIZE:
            logging.critical('BUFFER IS TOO BIG! Cutting down to %d', self._MESSAGEBUFFER_CUT_SIZE)
            self._message_buffer = self._message_buffer[-self._MESSAGEBUFFER_CUT_SIZE:]  # note negative index

        if bytes_available_int > 3500:   # rpi serial buffer is 4k. If we are starting to get close, we need to flush
            # dump _message_buffer and try to get the last complete message
            # if there isn't one, get everything in the serial buffer from last startOfHeader onwards!
            logging.error('Buffer overflow! Serial available %d. Purging', bytes_available_int)
            new_bytes = self.ser.read(bytes_available_int).decode('ASCII')
            last_start_index = new_bytes.rfind(chr(self._kStartOfHeaderByte))
            if last_start_index == -1:  # if we can't find a start, this is an error.
                logging.error("Can't find startOfHeader in data after overflow. Is message size too big (>2k)?")
                logging.debug('new data: %s', new_bytes)
                self._message_buffer = ''  # No point in storing new_bytes, it doesn't have a start - can't be parsed
                return None
            else:           # If we can find start, try to find another start before it and hope its a good message
                prior_start_index = new_bytes[:last_start_index].rfind(chr(self._kStartOfHeaderByte))
                if prior_start_index == -1:     # If there is only one start, wait for a full message
                    self._message_buffer = new_bytes[last_start_index:]
                    while True:                 # block here until we get a full message
                        single_message = self._acquireNewTransmission()
                        if single_message is not None:
                            return single_message
                else:           # If we can find another start before the last, keep it and everything after
                    self._message_buffer = new_bytes[prior_start_index:]
        else:  # everything ok, just append all the new data
            self._message_buffer += self.ser.read(bytes_available_int).decode('ASCII')

        # try to get everything up to the endOfTransmission
        end_index = self._message_buffer.find(chr(self._kEndOfTransmissionByte))
        if end_index == -1:  # no endOfTransmission, just return None
            return None

        single_message = self._message_buffer[:end_index+1]   # python slices up to, but not including, the end index
        self._message_buffer = self._message_buffer[end_index+1:]
        return single_message

    @staticmethod
    def _compareChecksums(crc_received, message):
        crc8 = Crc8()
        if crc_received != crc8.digest(message):
            logging.error("Checksums do not match")
            raise ConnectionError
        return 1
