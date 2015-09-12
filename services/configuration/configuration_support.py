import configuration as cf
import communication

def GetInstruction(instruction, instruction_code, message):
	start_instruction = message.find(instruction_code)
	end_instruction = message.find("\"",start_instruction)
	instruction.code = message[start_instruction : end_instruction]

	start_id = message.find("{",end_instruction) + 1
	end_id = message.find(",",start_id)
	instruction.id = int(message[start_id : end_id])

	start_parameter = end_id + 1;
	end_parameter = message.find("}",start_parameter)
	instruction.parameter = message[start_parameter : end_parameter]

	return instruction

def GetInstructionParameter(instruction_code, instruction_id, message):
	search_string = instruction_code + "\":{" + str(instruction_id) + ",";
	start_parameter = message.find(search_string) + len(search_string)
	end_parameter = message.find("}", start_parameter)
	return message[start_parameter : end_parameter]

def HandleErrorInstructions(state, instruction, instruction_code, message):
	state.error_codes = []
	state.error_parameters = []
	start = -1
	end = len(message)
	while True:
		start = message.find(instruction_code, start + 1)
		if (start != -1):
			instruction = GetInstruction(instruction, instruction_code, message[start:end])	
			state.error_codes.append(instruction.id)
			state.error_parameters.append(instruction.parameter[1:len(instruction.parameter)-1]) # take off quotes
		else:
			return state

def HandleRecipeInstruction(state, recipe_instruction, message):
	if (message == ""):
		state.end_of_recipe = True
		return state

	start_time = 0
	end_time = message.find(" ")
	state.recipe_time = float(message[start_time : end_time])

	start_code = message.find(" ") + 1
	end_code = message.find(" ",start_code)
	state.recipe_code = message[start_code : end_code]

	start_parameter = end_code + 1;
	end_parameter = len(message)
	state.recipe_parameter = message[start_parameter : end_parameter]

	return state


def HandleUserMessage(state, message):
	# Handle Display Message
	if (message == "DIS"):
		state.Display()
	return state


def HandleRecipe(state, recipe_file):
	# Read and execute all recipe instructions that are at or before current time
	while True:
		# Only read new recipe instruction if have executed previous one
		if (state.recipe_instruction_waiting == False):
			message = recipe_file.readline()
			state = HandleRecipeInstruction(state, cf.RecipeInstruction, message)

		# Check For Start and End Of Recipe
		if (state.start_of_recipe == True):
			print ("Starting New Recipe!")
			state.recipe_start_time = state.time
			state.start_of_recipe = False
		if (state.end_of_recipe == True):
			print("Recipe Finished. Time to Harvest!")
			return state

		# If Valid, Execute Instruction
		if (state.time >= state.recipe_time + state.recipe_start_time):
			state = cf.ExecuteRecipeInstruction(state)
			state.recipe_instruction_waiting = False

		else:
			state.recipe_instruction_waiting = True
			return state

def ComputeDirection(desired, reported, threshold):
	if (desired < reported - threshold):
		return -1
	elif (desired > reported + threshold):
		return 1
	else:
		return 0

def SendInstruction(ser, code, id, parameter):
	message = code + " " + str(id) + " " + str(parameter)
	print (message)
	communication.Send(ser,message)


