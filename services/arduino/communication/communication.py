import time, serial, select, sys

# Public
def Begin(ser, timeout, verbosity=False):
	ReciprocateNewConnection(ser, timeout, verbosity=verbosity)

def Send(ser, message, verbosity=False):
	if (verbosity):
		print(("Sending: " + message))
	packed_message = chr(1) # start of header
	packed_message += str(len(message))
	packed_message += chr(2) # start of text
	packed_message += message
	packed_message += chr(3) # end of text
	crc8 = Crc8();
	packed_message += str(crc8.digest(message))
	packed_message += chr(4) # end of transmission
	ser.write(bytes(packed_message, 'UTF-8'))

def Receive(ser, timeout, verbosity=False):
	# Acquire New Messages
	incoming_message = ""
	incoming_message = AcquireNewTransmission(ser, timeout, verbosity)
	# Parse Header
	message_length = ParseHeader(incoming_message, verbosity)
	if (message_length == 0):
		return ""
	# Parse Text
	message = ParseText(incoming_message, verbosity);
	if (message == ""):
		return ""
	# Parse Footer
	crc_received = ParseFooter(incoming_message, verbosity)
	if (crc_received == 256):
		return ""
	# Compute Crc8
	if (CompareChecksums(crc_received, message, verbosity) == 0):
		return ""
	return message;


def GetUserMessage():
	i, o, e = select.select( [sys.stdin], [], [], 0.100 )
	if (i):
		return str(sys.stdin.readline().strip())
	else:
		return ""
	return s

# ASCII Controls
kStartOfHeaderByte = 1
kStartOfTextByte = 2
kEndOfTextByte = 3
kEndOfTransmissionByte = 4
kEnquireByte = b'\x05'
kAcknowledgeByte = b'\x06'

# Class Definitions
class Crc8(object):
	TABLE=[
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

	def __init__(self, sum=0x00):
		self.sum=sum

	def _update(self, b):
		self.sum=self.TABLE[self.sum^b]

	def digest(self, st):
		self.sum=0
		for ch in st:
			self._update(ord(ch))
		return self.sum

# Function Definitions
def ReciprocateNewConnection(ser, timeout, verbosity=False):
	start_time = time.time()
	print ("\"Establishing new connection\"")
	#print ("\"Awaiting enq\"")
	while True:
		if (time.time() - start_time > timeout):
			if (verbosity):
				print ("\"Timed out\"")
			print ("\"Failure\"")
			return 0
		incoming_char = ser.read()
		if (incoming_char != b''):
			if (incoming_char == kEnquireByte):
				if (verbosity):
					print ("\"Received enquiry\"")
					print ("\"Sending acknowledge\"")
				ser.write(kAcknowledgeByte)
				if (verbosity):
					print ("\"Awaiting acknowledge\"")
				while True:
					if (time.time() - start_time > timeout):
						if (verbosity):
							print ("\"Timed out\"")
						print ("\"Failure\"")
						return 0
					incoming_char = ser.read()
					if (incoming_char != ""):
						if(incoming_char == kAcknowledgeByte):
							if (verbosity):
								print ("\"Received acknowledgement\"")
							print(("\"Success\":" + str(time.time() - start_time)))
							return 1


def AcquireNewTransmission(ser, timeout, verbosity=False):
	while True:
		start_time = time.time()
		if (ser.inWaiting()):
			incoming_byte = int.from_bytes(ser.read(), byteorder='big')
			if (incoming_byte == kStartOfHeaderByte):
				incoming_string = chr(incoming_byte)
				while True:
					if (ser.inWaiting()):
						incoming_byte = int.from_bytes(ser.read(), byteorder='big')
						incoming_string += chr(incoming_byte)
						if (incoming_byte == kEndOfTransmissionByte):
							return incoming_string						
					if (time.time() - start_time > timeout):
						if (verbosity):
							print ("Timed out")
							print ("Failed to acquire new message")
							return ""
		if (time.time() - start_time > timeout):
			if (verbosity):
				print ("Timed out")
				print ("Failed to acquire new message")
				return ""

def ParseHeader(message, verbosity=False):
	start = 1
	end = message.find(chr(kStartOfTextByte))
	if (end <= start):
		return 0
	value_string = message[start:end]
	if (value_string != ""):
		return int(value_string)
	else:
		return 0

def ParseText(message, verbosity=False):
	start = message.find(chr(kStartOfTextByte)) + 1
	end = message.find(chr(kEndOfTextByte))
	if (end <= start):
		return ""
	return message[start:end]

def ParseFooter(message, verbosity=False):
	start = message.find(chr(kEndOfTextByte)) + 1
	end = message.find(chr(kEndOfTransmissionByte))
	if (end <= start):
		return 256
	value_string = message[start:end]
	if (value_string != ""):
		return int(value_string)
	else:
		return 256

def CompareChecksums(crc_received, message, verbosity=False):
	crc8 = Crc8()
	if(crc_received != crc8.digest(message)):
		if (verbosity):
			print ("Checksums do not match")
			print ("Failed")
		return 0
	return 1