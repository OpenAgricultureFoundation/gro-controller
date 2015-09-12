import configuration_support as cs
from datetime import datetime
import time, communication

class SerialParameters(object):
	baud_rate = 9600
	establish_connection_timeout = 2 # seconds
	serial_read_timeout = 0.01 # seconds
	receive_message_timeout = 3 # seconds

class Instruction(object):
	code = ""
	id = 0
	parameter = ""

class RecipeInstruction(object):
	time = 0.0
	code = ""
	id = ""
	parameter = ""

class InstructionCode(object):
	error = "ERR"
	sensor_time = "STM"
	sensor_air_temperature = "SAT"
	sensor_air_humidity = "SHU"
	sensor_light_intensity = "SLI"
	actuator_air_heater = "AAH"
	actuator_air_humidifier = "AHU"
	actuator_air_vent = "AAV"
	actuator_air_circulation = "AAC"
	actuator_light_panel = "ALP"
	actuator_light_vent = "ALV"

class InstructionCodeExpanded(object):
	error = "Error"
	sensor_time = "Sensor Time"
	sensor_air_temperature = "Sensor Air Temperature"
	sensor_air_humidity = "Sensor Humidity"
	sensor_light_intensity = "Sensor Light Intensity"
	actuator_air_heater = "Actuator Air Heater"
	actuator_air_humidifier = "Actuator Air Humidifier"
	actuator_air_vent = "Actuator Air Vent"
	actuator_air_circulation = "Actuator Air Circulation"
	actuator_light_panel = "Actuator Light Panel"
	actuator_light_vent = "Actuator Light Vent"

class State(object):
	# Non-configurable
	mode = 0
	time = 0.0
	start_of_recipe = True
	end_of_recipe = False
	recipe_instruction_waiting = False
	recipe_start_time = 0.0
	recipe_time = 0.0
	recipe_code = ""
	recipe_parameter = ""
	error_codes = []
	error_parameters = []

	reported_sensor_time_default = "26/07/2015 21:51:53"
	reported_sensor_time_default_id = 1

	# Air Temperature Sensor
	# Reported
	reported_sensor_air_temperature_default = 0.0
	reported_sensor_air_temperature_default_id = 1
	# Controls
	desired_sensor_air_temperature_default = 0.0
	ambient_sensor_air_temperature_1 = 21.0
	active_actuation_sensor_air_temperature_1 = False
	active_threshold_sensor_air_temperature_1 = .5 # kind of like overshoot
	inactive_threshold_sensor_air_temperature_1 = 1 # level of precision we strive to maintain
	direction_sensor_air_temperature_1 = 0

	# Air Humidity Sensor
	# Reported
	reported_sensor_air_humidity_default = 0.0
	reported_sensor_air_humidity_default_id = 1
	# Controls
	desired_sensor_air_humidity_default = 0.0
	ambient_sensor_air_humidity_1 = 45
	active_actuation_sensor_air_humidity_1 = False
	active_threshold_sensor_air_humidity_1 = 2
	inactive_threshold_sensor_air_humidity_1 = 4
	direction_sensor_air_humidity_1 = 0

	# Light Intensity Sensor
	# Reported
	reported_sensor_light_intensity_default = 0.0
	reported_sensor_light_intensity_default_id = 1
	# Controls
	desired_sensor_light_intensity_default = 0.0
	ambient_sensor_light_intensity_defaul1 = 45
	active_actuation_sensor_light_intensity_1 = False
	active_threshold_sensor_light_intensity_1 = 2
	inactive_threshold_sensor_light_intensity_1 = 4
	direction_sensor_light_intensity_1 = 0

	# Air Heater Actuator
	# Controls
	desired_actuator_air_heater_default = 0
	desired_actuator_air_heater_default_id = 1

	# Air Humidifier Actuator
	# Controls
	desired_actuator_air_humidifier_default = 0
	desired_actuator_air_humidifier_default_id = 1

	# Air Vent Actuator
	# Controls
	desired_actuator_air_vent_default = 0
	desired_actuator_air_vent_default_id = 1

	# Air Circulation Actuator
	# Controls
	desired_actuator_air_circulation_default = 0
	desired_actuator_air_circulation_default_id = 1

	# Light Panel Actuator
	# Controls
	desired_actuator_light_panel_default = 0
	desired_actuator_light_panel_default_id = 1
	
	# Light Fan Actuator
	# Controls
	desired_actuator_light_vent_default = 0
	desired_actuator_light_vent_default_id = 1

	# Display State
	def Display(self):
		print(("mode = " + str(self.mode)))
		print(("error_codes = " + str(self.error_codes)))
		print(("error_parameters = " + str(self.error_parameters)))
		print(("reported_sensor_time_default = " + str(self.reported_sensor_time_default)))
		print(("reported_sensor_air_temperature_default = " + str(self.reported_sensor_air_temperature_default)))
		print(("reported_sensor_air_humidity_default = " + str(self.reported_sensor_air_humidity_default)))
		print(("reported_sensor_light_intensity_default = " + str(self.reported_sensor_light_intensity_default)))
		print(("desired_sensor_air_temperature_default = " + str(self.desired_sensor_air_temperature_default)))
		print(("desired_sensor_air_humidity_default = " + str(self.desired_sensor_air_humidity_default)))
		print(("desired_sensor_light_intensity_default = " + str(self.desired_sensor_light_intensity_default)))
		print(("desired_actuator_air_heater_default = " + str(self.desired_actuator_air_heater_default)))
		print(("desired_actuator_air_humidifier_default = " + str(self.desired_actuator_air_humidifier_default)))
		print(("desired_actuator_air_vent_default = " + str(self.desired_actuator_air_vent_default)))
		print(("desired_actuator_air_circulation_default = " + str(self.desired_actuator_air_circulation_default)))
		print(("desired_actuator_light_panel_default = " + str(self.desired_actuator_light_panel_default)))
		print(("desired_actuator_light_vent_default = " + str(self.desired_actuator_light_vent_default)))

	# Generate Message for Log
	def GetLogMessage(self):
		# Sensors
		message = "{\"" + InstructionCode.sensor_time + "\":" + str(self.time) + ","
		message += "\"d" + InstructionCode.sensor_air_temperature + "\":" + str(self.desired_sensor_air_temperature_default) + ","
		message += "\"" + InstructionCode.sensor_air_temperature + "\":" + str(self.reported_sensor_air_temperature_default) + ","
		message += "\"d" + InstructionCode.sensor_air_humidity + "\":" + str(self.desired_sensor_air_humidity_default) + ","
		message += "\"" + InstructionCode.sensor_air_humidity + "\":" + str(self.reported_sensor_air_humidity_default) + ","
		message += "\"d" + InstructionCode.sensor_light_intensity + "\":" + str(self.desired_sensor_light_intensity_default) + ","
		message += "\"" + InstructionCode.sensor_light_intensity + "\":" + str(self.reported_sensor_light_intensity_default) + ","

		# Actuators
		message += "\"" + InstructionCode.actuator_air_heater + "\":" + str(self.desired_actuator_air_heater_default) + ","
		message += "\"" + InstructionCode.actuator_air_humidifier + "\":" + str(self.desired_actuator_air_humidifier_default) + ","
		message += "\"" + InstructionCode.actuator_air_vent + "\":" + str(self.desired_actuator_air_vent_default) + ","
		message += "\"" + InstructionCode.actuator_air_circulation + "\":" + str(self.desired_actuator_air_circulation_default) + ","
		message += "\"" + InstructionCode.actuator_light_panel + "\":" + str(self.desired_actuator_light_panel_default) + ","
		message += "\"" + InstructionCode.actuator_light_vent + "\":" + str(self.desired_actuator_light_vent_default) + ","

		# Errors
		for i in range(0,len(self.error_codes)):
			message += "\"" + InstructionCode.error + "\":\"" + str(self.error_codes[i]) + "-" + str(self.error_parameters[i]) + "\"," 

		# End of Message
		message += "\"END\":0},\n"
		return message


def HandleStreamMessage(state, message):
	# Handle Time
	state.reported_sensor_time_default = cs.GetInstructionParameter(InstructionCode.sensor_time, state.reported_sensor_time_default_id, message)
	# d = datetime.strptime(state.reported_sensor_time_default, "%d/%m/%Y %H:%M:%S")
	# state.time = time.mktime(d.timetuple())
	# Handle Error Messages
	state = cs.HandleErrorInstructions(state, Instruction, InstructionCode.error, message)
	# Handle Rest of Stream
	state.reported_sensor_air_temperature_default = float(cs.GetInstructionParameter(InstructionCode.sensor_air_temperature, state.reported_sensor_air_temperature_default_id, message))
	state.reported_sensor_air_humidity_default = float(cs.GetInstructionParameter(InstructionCode.sensor_air_humidity, state.reported_sensor_air_humidity_default_id, message))
	# note: add in light intensity		

	return state

def ExecuteRecipeInstruction(state):
	if (state.recipe_code == InstructionCode.sensor_air_temperature):
		print(("@ " + state.reported_sensor_time_default + " -> " + str(state.recipe_code) + " " + str(state.recipe_parameter)))
		state.desired_sensor_air_temperature_default = float(state.recipe_parameter)
	if (state.recipe_code == InstructionCode.sensor_air_humidity):
		print(("@ " + state.reported_sensor_time_default + " -> " + str(state.recipe_code) + " " + str(state.recipe_parameter)))
		state.desired_sensor_air_humidity_default = float(state.recipe_parameter)

	if (state.recipe_code == InstructionCode.sensor_light_intensity):
		print(("@ " + state.reported_sensor_time_default + " -> " + str(state.recipe_code) + " " + str(state.recipe_parameter)))
		state.desired_sensor_light_intensity_default = float(state.recipe_parameter)

	return state


TemperatureHumidityDirectionDecisionTable = [
	# T, H, (:) HE, HU, V, C
	[-1,-1,0,0,1,1],
	[-1,0,0,0,1,1],
	[-1,1,0,1,1,1],
	[0,-1,0,0,1,1],
	[0,0,0,0,0,1],
	[0,1,0,1,0,1],
	[1,-1,1,0,1,1],
	[1,0,1,0,0,1],
	[1,1,1,1,0,1],
]

def HandleControls(state, ser):
	# Get Direction Based off Active/Inactive Threshold
	# Air Temperature
	if (state.active_actuation_sensor_air_temperature_1 == False):
		state.direction_sensor_air_temperature_1 = cs.ComputeDirection(state.desired_sensor_air_temperature_default, state.reported_sensor_air_temperature_default, state.inactive_threshold_sensor_air_temperature_1)
	else:
		state.direction_sensor_air_temperature_1 = cs.ComputeDirection(state.desired_sensor_air_temperature_default, state.reported_sensor_air_temperature_default, state.active_threshold_sensor_air_temperature_1)
	# Humidity
	if (state.active_actuation_sensor_air_humidity_1 == False):
		state.direction_sensor_air_humidity_1 = cs.ComputeDirection(state.desired_sensor_air_humidity_default, state.reported_sensor_air_humidity_default, state.inactive_threshold_sensor_air_humidity_1)
	else:
		state.direction_sensor_air_humidity_1 = cs.ComputeDirection(state.desired_sensor_air_humidity_default, state.reported_sensor_air_humidity_default, state.active_threshold_sensor_air_humidity_1)

	# Get Desired Temperature and Humidity State From Direction Based Lookup Table
	for i in range(0,len(TemperatureHumidityDirectionDecisionTable)):
		if ((TemperatureHumidityDirectionDecisionTable[i][0] == state.direction_sensor_air_temperature_1) & (TemperatureHumidityDirectionDecisionTable[i][1] == state.direction_sensor_air_humidity_1)):
			# Actuator Air Heater
			desired = TemperatureHumidityDirectionDecisionTable[i][2]
			if (state.desired_actuator_air_heater_default != desired):
				state.desired_actuator_air_heater_default = desired
				cs.SendInstruction(ser, InstructionCode.actuator_air_heater, state.desired_actuator_air_heater_default_id, state.desired_actuator_air_heater_default)
			# Actuator Air Humidifier
			desired = TemperatureHumidityDirectionDecisionTable[i][3]
			if (state.desired_actuator_air_humidifier_default != desired):
				state.desired_actuator_air_humidifier_default = desired
				cs.SendInstruction(ser, InstructionCode.actuator_air_humidifier, state.desired_actuator_air_humidifier_default_id, state.desired_actuator_air_humidifier_default)
			# Actuator Air Vent
			desired = TemperatureHumidityDirectionDecisionTable[i][4]
			if (state.desired_actuator_air_vent_default != desired):
				state.desired_actuator_air_vent_default = desired
				cs.SendInstruction(ser, InstructionCode.actuator_air_vent, state.desired_actuator_air_vent_default_id, state.desired_actuator_air_vent_default)
			# Actuator Air Circulation
			desired = TemperatureHumidityDirectionDecisionTable[i][5]
			if (state.desired_actuator_air_circulation_default != desired):
				state.desired_actuator_air_circulation_default = desired
				cs.SendInstruction(ser, InstructionCode.actuator_air_circulation, state.desired_actuator_air_circulation_default_id, state.desired_actuator_air_circulation_default)


	# Set Light Panel and Light Vent On if Desired Light Intensity > 0
	desired = state.desired_sensor_light_intensity_default
	if (desired > 0):
		desired = 1
	# Light Panel
	if (state.desired_actuator_light_panel_default != desired):
		state.desired_actuator_light_panel_default = desired
		cs.SendInstruction(ser, InstructionCode.actuator_light_panel, state.desired_actuator_light_panel_default_id, state.desired_actuator_light_panel_default)
	# Light Vent
	if (state.desired_actuator_light_vent_default != desired):
		state.desired_actuator_light_vent_default = desired
		cs.SendInstruction(ser, InstructionCode.actuator_light_vent, state.desired_actuator_light_vent_default_id, state.desired_actuator_light_vent_default)

	return state
























