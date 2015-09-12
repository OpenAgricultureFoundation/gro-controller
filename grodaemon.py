import time, serial, communication, configuration, configuration_support

# instruction_code = configuration.InstructionCode()
# instruction_code_extended = configuration.InstructionCodeExpanded()
state = configuration.State()
serial_parameters = configuration.SerialParameters()

# Main Code
if __name__=="__main__":
	# Initialization Code (INIT)
	# Initialize Serial Communication
	ser = serial.Serial("/dev/tty.usbmodem1411", baudrate=serial_parameters.baud_rate, timeout=serial_parameters.serial_read_timeout)
	recipe_file = open("recipe.gro")
	log_file = open("recipe.log",'w')
	start_time = time.time()
	if(communication.Begin(ser, serial_parameters.establish_connection_timeout, verbosity=True) == False):
		while True:
			"begin coping with eternal silence"

	while True:
		# Handle Stream Message
		stream_message = communication.Receive(ser, serial_parameters.receive_message_timeout, True)
		if (stream_message != ""):
			state = configuration.HandleStreamMessage(state, stream_message)
		# Handle Recipe
		state = configuration_support.HandleRecipe(state, recipe_file)
		# Handle Controls
		state = configuration.HandleControls(state, ser)
		# Log Data
		log_file.write(state.GetLogMessage())
		# Handle User Message
		user_message = communication.GetUserMessage()
		if (user_message != ""):
			state = configuration_support.HandleUserMessage(state, user_message)