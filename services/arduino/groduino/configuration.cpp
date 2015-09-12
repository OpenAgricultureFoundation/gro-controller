// Include Files
#include "general_configuration.h"
#include "general_communication.h"
#include "sensor_ds1307.h"
#include "sensor_dht22.h"
#include "actuator_relay.h"


// Declare Structures
struct Pins {
  const int sensor_dht22_air_temperature_humidity_default_pin = A0;
  const int actuator_relay_air_heater_default_pin = 3;
  const int actuator_relay_air_humidifier_default_pin = 2;
  const int actuator_relay_air_vent_default_pin = 10;
  const int actuator_relay_air_circulation_default_pin = 8;
  const int actuator_relay_light_panel_default_pin = 4;
  const int actuator_relay_light_vent_default_pin = 12;
} pins;

struct Instructions {
  const String sensor_time = "STM";
  const String sensor_air_temperature = "SAT";
  const String sensor_air_humidity = "SHU";
  const String actuator_air_heater = "AAH";
  const String actuator_air_humidifier = "AHU";
  const String actuator_air_vent = "AAV";
  const String actuator_air_circulation = "AAC";
  const String actuator_light_panel = "ALP";
  const String actuator_light_vent = "ALV";
} instructions;

// Declare Objects
Communication communication;
SensorDs1307 sensor_ds1307_time_default(1, instructions.sensor_time);
SensorDht22 sensor_dht22_air_temperature_humidity_default(1, pins.sensor_dht22_air_temperature_humidity_default_pin, instructions.sensor_air_humidity, instructions.sensor_air_temperature);
ActuatorRelay actuator_relay_air_heater_default(1, pins.actuator_relay_air_heater_default_pin, instructions.actuator_air_heater);
ActuatorRelay actuator_relay_air_humidifier_default(1, pins.actuator_relay_air_humidifier_default_pin, instructions.actuator_air_humidifier);
ActuatorRelay actuator_relay_air_vent_default(1, pins.actuator_relay_air_vent_default_pin, instructions.actuator_air_vent);
ActuatorRelay actuator_relay_air_circulation_default(1, pins.actuator_relay_air_circulation_default_pin, instructions.actuator_air_circulation);
ActuatorRelay actuator_relay_light_panel_default(1, pins.actuator_relay_light_panel_default_pin, instructions.actuator_light_panel);
ActuatorRelay actuator_relay_light_vent_default(1, pins.actuator_relay_light_vent_default_pin, instructions.actuator_light_vent);

// Configuration Functions
void InitializeConfiguration(void) {
  communication.begin();
  sensor_ds1307_time_default.begin();
  sensor_dht22_air_temperature_humidity_default.begin();
  actuator_relay_air_heater_default.begin();
  actuator_relay_air_humidifier_default.begin();
  actuator_relay_air_vent_default.begin();
  actuator_relay_air_circulation_default.begin();
  actuator_relay_light_panel_default.begin();
  actuator_relay_light_vent_default.begin();
}

void UpdateConfiguration(void) {
  // Check for Message and Handle if Necessary
  String return_message = "";
  while (communication.available()) { // read in message until nothing in serial buffer or message handler generates a return message
    return_message = HandleIncomingMessage();
    if (return_message != "") {
      break;
    }
  }
  // Update and Send the Data Stream
  String message = "";
  message += sensor_ds1307_time_default.get();
  message += sensor_dht22_air_temperature_humidity_default.get();
  message += actuator_relay_air_heater_default.get();
  message += actuator_relay_air_humidifier_default.get();
  message += actuator_relay_air_vent_default.get();
  message += actuator_relay_air_circulation_default.get();
  message += actuator_relay_light_panel_default.get();
  message += actuator_relay_light_vent_default.get();
  message += return_message + "\"ERR\":{4,\"bad things\"}";
  communication.send(message);
}

String HandleIncomingMessage(void) {
  String instruction = communication.receive();
  String return_message;
  if (instruction.length() < 3) {
    return "";
  }

  // Sensors
  if (sensor_ds1307_time_default.set(instruction)) {return "";}
  if (sensor_dht22_air_temperature_humidity_default.set(instruction)) {return "";}
  
  // Actuators
  return_message = actuator_relay_air_heater_default.set(instruction);
  if (return_message != "") { return return_message;}
  
  return_message = actuator_relay_air_humidifier_default.set(instruction);
  if (return_message != "") { return return_message;}
  
  return_message = actuator_relay_air_vent_default.set(instruction);
  if (return_message != "") { return return_message;}
  
  return_message = actuator_relay_air_circulation_default.set(instruction);
  if (return_message != "") { return return_message;}

  return_message = actuator_relay_light_panel_default.set(instruction);
  if (return_message != "") { return return_message;}
  
  return_message = actuator_relay_light_vent_default.set(instruction);
  if (return_message != "") { return return_message;}
  
  return "";
}

