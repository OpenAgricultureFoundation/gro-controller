//---------------------------------------STATIC MODULE HANDLER CODE----------------------------------//
#include "module_handler.h"


// Declare Communication Object
Communication communication(0); // 1 to listen

// Function(initializeStaticModules): called once to initialize all static modules
void initializeStaticModules(void) {
  communication.begin();
}

// Function(updateIncomingMessage): if new message is available, receive message and pass to
// handler function. If handler function returns response message, send out
void updateIncomingMessage(void) {
  // Check for Message(s) And Handle If Necessary
  String response_message = "";
  while (communication.available()) { // read in message(s) until nothing in serial buffer
    response_message += handleIncomingMessage();
  }
  // Append Responses From Message(s) Then Send
  if (response_message != "") {
    response_message = "\"GTYP\":\"Response\"," + response_message;
    response_message += "\"GEND\":0";
    communication.send(response_message);
  }
}

// Function(parseIncomingMessage): breaks incoming message into 3 parts: Instruction Code,
// Instruction ID, Instruction Parameter then returns the parts as an Instruction Object
// Also, the Instruction Valid parameter is set accordingly.
Instruction parseIncomingMessage(String message) {
  // Initialize Instruction
  Instruction instruction;
  instruction.valid = 0;

  // Get Instruction Data
  int len = message.length();
  int first_space = message.indexOf(" ");
  if ((first_space > 0) && (len > first_space)) {
    int second_space = message.indexOf(" ", first_space + 1);
    if ((second_space > 0) && (second_space < len - 1)) {
      // Received good message
      instruction.code = message.substring(0,4);
      instruction.id = (message.substring(first_space, second_space)).toInt();
      instruction.parameter = message.substring(second_space + 1, len);
      instruction.valid = 1;
    }
  }

  // Return Instruction Data
  return instruction;
}

//---------------------------------------DYNAMIC MODULE HANDLER CODE---------------------------------//
// Import Module Libraries
#include "sensor_ds1307.h"
#include "sensor_tsl2561.h"
#include "sensor_dht22.h"
#include "sensor_gc0011.h"
#include "sensor_dfr0161.h"
#include "actuator_relay.h"
#include "sensor_dfr0300.h"
#include "sensor_contact_switch.h"

// Electronics Panel Iteration2
SensorTsl2561 sensor_tsl2561_light_intensity_default("SLIN", 1, "SLPA", 1);
SensorDht22 sensor_dht22_air_temperature_humidity_default(A0, "SATM", 1, "SAHU", 1);
SensorGc0011 sensor_gc0011_air_co2_temperature_humidity_default(12, 11, "SACO", 1, "SATM", 2, "SAHU", 2);
SensorDfr0161 sensor_dfr0161_water_ph_default(A1, "SWPH", 1);
SensorDfr0300 sensor_dfr0300_water_temperature_ec_default(5, A2, 2, "SWTM", 1, "SWEC", 1);
SensorContactSwitch sensor_contact_switch_general_shell_open_default(4, "SGSO", 1); 
SensorContactSwitch sensor_contact_switch_general_window_open_default(3, "SGWO", 1);

// AC Relay Block: AC[1:4] <--> Pin[9:6]
// pin 6 --> port 4
ActuatorRelay actuator_relay_air_heater_default(6, "AAHE", 1); // AC port 4
ActuatorRelay actuator_relay_light_panel_default(8, "ALPN", 1); // AC port 2
ActuatorRelay actuator_relay_air_humidifier_default(9, "AAHU", 1); // AC port 1

// DC Relay Block 
ActuatorRelay actuator_relay_air_vent_default(14, "AAVE", 1); 
ActuatorRelay actuator_relay_air_circulation_default(15, "AACR", 1);   
ActuatorRelay actuator_relay_light_chamber_illumination_default(53, "ALPN", 4);  // ALCI                                                             
ActuatorRelay actuator_relay_light_motherboard_illumination_default(52, "ALMI", 1);

/*
  // Electronics Panel Iteration1
  SensorTsl2561 sensor_tsl2561_light_intensity_default("SLIN", 1);
  SensorDht22 sensor_dht22_air_temperature_humidity_default(A0, "SATM", 1, "SAHU", 1);
  SensorGc0011 sensor_gc0011_air_co2_temperature_humidity_default(11, 12, "SACO", 1, "SATM", 2, "SAHU", 2);
  SensorDfr0300 sensor_dfr0300_water_temperature_ec_default(2, A2, "SWTM", 1, "SWEC", 1); //attn
  SensorDfr0161 sensor_dfr0161_water_ph_default(A1, "SWPH", 1);
  
  ActuatorRelay actuator_relay_light_panel_default(6, "ALPN", 1);
  ActuatorRelay actuator_relay_light_vent_default(4, "ALVE", 1); //attn
  ActuatorRelay actuator_relay_air_heater_default(7, "AAHE", 1);
  ActuatorRelay actuator_relay_air_humidifier_default(8, "AAHU", 1);
  ActuatorRelay actuator_relay_air_vent_default(3, "AAVE", 1);
  ActuatorRelay actuator_relay_air_circulation_default(5, "AACR", 1);
*/

/*
  // Wooden Box
  SensorDs1307 sensor_ds1307_time_default("GTIM",1);
  SensorTsl2561 sensor_tsl2561_light_intensity_default("SLIN", 1);
  SensorDht22 sensor_dht22_air_temperature_humidity_default(A0, "SATM", 1, "SAHU", 1);
  SensorGc0011 sensor_gc0011_air_co2_temperature_humidity_default(11, 12, "SACO", 1, "SATM", 2, "SAHU", 2);
  SensorDfr0300 sensor_dfr0300_water_temperature_ec_default(7, A2, "SWTM", 1, "SWEC", 1);
  SensorDfr0161 sensor_dfr0161_water_ph_default(A1, "SWPH", 1);
  ActuatorRelay actuator_relay_light_panel_default(4, "ALPN", 1);
  ActuatorRelay actuator_relay_light_vent_default(12, "ALVE", 1);
  ActuatorRelay actuator_relay_air_heater_default(3, "AAHE", 1);
  ActuatorRelay actuator_relay_air_humidifier_default(2, "AAHU", 1);
  ActuatorRelay actuator_relay_air_vent_default(10, "AAVE", 1);
  ActuatorRelay actuator_relay_air_circulation_default(8, "AACR", 1);
*/

// Function(initializeDynamicModules): called once to initialize all dynamic modules
void initializeDynamicModules(void) {
  sensor_tsl2561_light_intensity_default.begin();
  sensor_dht22_air_temperature_humidity_default.begin();
  sensor_gc0011_air_co2_temperature_humidity_default.begin();
  sensor_dfr0161_water_ph_default.begin();
  sensor_dfr0300_water_temperature_ec_default.begin();
  sensor_contact_switch_general_shell_open_default.begin();
  sensor_contact_switch_general_window_open_default.begin();
  actuator_relay_air_heater_default.begin();
  actuator_relay_air_humidifier_default.begin();
  actuator_relay_air_vent_default.begin();
  actuator_relay_air_circulation_default.begin();
  actuator_relay_light_panel_default.begin();
  actuator_relay_light_chamber_illumination_default.begin();
  actuator_relay_light_motherboard_illumination_default.begin();

  // Set Default States
  actuator_relay_air_circulation_default.set("AACR", 1, "1");
  actuator_relay_light_motherboard_illumination_default.set("ALMI",1,"1");
}


// Function(updateStreamMessage):  polls all objects and appends to message stream
// note: all apended data must be in JSON format
void updateStreamMessage(void) {
  // Initialize Stream Message
  String stream_message = "\"GTYP\":\"Stream\",";
  
  // Get Stream Message
  stream_message += sensor_dfr0300_water_temperature_ec_default.get();
  stream_message += sensor_tsl2561_light_intensity_default.get();
  stream_message += sensor_dht22_air_temperature_humidity_default.get(); // does not work on 1.0
  stream_message += sensor_gc0011_air_co2_temperature_humidity_default.get();
  stream_message += sensor_dfr0161_water_ph_default.get();
  stream_message += sensor_contact_switch_general_shell_open_default.get();
  stream_message += sensor_contact_switch_general_window_open_default.get();
  stream_message += sensor_dfr0161_water_ph_default.get();
  stream_message += actuator_relay_air_heater_default.get();
  stream_message += actuator_relay_air_humidifier_default.get();
  stream_message += actuator_relay_air_vent_default.get();
  stream_message += actuator_relay_air_circulation_default.get();
  stream_message += actuator_relay_light_panel_default.get();
  stream_message += actuator_relay_light_chamber_illumination_default.get();
  stream_message += actuator_relay_light_motherboard_illumination_default.get();
  
  // Return Stream Message
  stream_message += "\"GEND\":0";
  
  // Send Stream Message
  communication.send(stream_message);
}

// Function (handleIncomingMessage): incoming messages get passed into this function. Messages are
// parsed into 3 main components: Instruction Code, Instruction ID, Instruction Parameter.
// These components are passed piecewise into all <module>.set functions. If a return message is 
// geneated from the <module>.set function, this function will return that message
String handleIncomingMessage(void) {
  // Parse Message into: Code - ID - Parameter
  String return_message = "";
  String incoming_message = communication.receive();
  Instruction instruction = parseIncomingMessage(incoming_message);

  // Pass Parsed Message To All Objects and Update Return Message if Applicable
  if (instruction.valid) {
    return_message += sensor_tsl2561_light_intensity_default.set(instruction.code, instruction.id, instruction.parameter);
    return_message += sensor_dht22_air_temperature_humidity_default.set(instruction.code, instruction.id, instruction.parameter);
    return_message += sensor_gc0011_air_co2_temperature_humidity_default.set(instruction.code, instruction.id, instruction.parameter);
    return_message += sensor_dfr0300_water_temperature_ec_default.set(instruction.code, instruction.id, instruction.parameter);
    return_message += sensor_dfr0161_water_ph_default.set(instruction.code, instruction.id, instruction.parameter);
    return_message += sensor_contact_switch_general_shell_open_default.set(instruction.code, instruction.id, instruction.parameter);
    return_message += sensor_contact_switch_general_window_open_default.set(instruction.code, instruction.id, instruction.parameter);
    return_message += actuator_relay_air_heater_default.set(instruction.code, instruction.id, instruction.parameter);
    return_message += actuator_relay_air_humidifier_default.set(instruction.code, instruction.id, instruction.parameter);
    return_message += actuator_relay_air_vent_default.set(instruction.code, instruction.id, instruction.parameter);
    return_message += actuator_relay_air_circulation_default.set(instruction.code, instruction.id, instruction.parameter);
    return_message += actuator_relay_light_panel_default.set(instruction.code, instruction.id, instruction.parameter);  
    return_message += actuator_relay_light_chamber_illumination_default.set(instruction.code, instruction.id, instruction.parameter);
    return_message += actuator_relay_light_motherboard_illumination_default.set(instruction.code, instruction.id, instruction.parameter);
  }
  return return_message;
}


