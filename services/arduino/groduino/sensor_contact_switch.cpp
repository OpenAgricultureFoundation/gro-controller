#include "sensor_contact_switch.h"

//--------------------------------------------------PUBLIC-------------------------------------------//
SensorContactSwitch::SensorContactSwitch(int pin, String instruction_code, int instruction_id) {
 pin_ = pin;
 instruction_code_ = instruction_code;
 instruction_id_ = instruction_id;
}

void SensorContactSwitch::begin(void) {
 pinMode(pin_,INPUT_PULLUP);
}

String SensorContactSwitch::get(void) {
  // Get Sensor Data
  is_connected_ = getData();

  // Initialize Message
  String message = "";

  // Append Actuator State
  message += "\"";
  message += instruction_code_;
  message += " ";
  message += instruction_id_;
  message += "\":";
  message += is_connected_;
  message += ",";

  // return "";
  return message;
}

String SensorContactSwitch::set(String instruction_code, int instruction_id, String instruction_parameter) {
  return "";
}

//-------------------------------------------------PRIVATE-------------------------------------------//
bool SensorContactSwitch::getData(void) {
  return digitalRead(pin_);
}

