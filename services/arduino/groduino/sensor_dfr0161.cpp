#include "sensor_dfr0161.h"

//-------------------------------------------------PUBLIC---------------------------------------------/
SensorDfr0161::SensorDfr0161(uint8_t pin, String instruction_code, int instruction_id) {
  instruction_id_ = instruction_id;
  pin_ = pin;
  instruction_code_ = instruction_code;
  offset_ = -0.66;
}

void SensorDfr0161::begin(void) {
}

String SensorDfr0161::get(void) {
  // Initialize Message
  String message = "\"";

  // Append pH
  message += instruction_code_;
  message += " ";
  message += instruction_id_;
  message += "\":";
  float value = analogRead(pin_)*5.0/1024*3.5 + offset_;
  message += floatToString(value, 100);
  message += ",";

  // Return Message
  return message;
}

String SensorDfr0161::set(String instruction_code, int instruction_id, String instruction_parameter) {
  return "";
}


String SensorDfr0161::floatToString(double val, unsigned int precision) {
// prints val with number of decimal places determine by precision
// NOTE: precision is 1 followed by the number of zeros for the desired number of decimial places
// example: printDouble( 3.1415, 100); // prints 3.14 (two decimal places)
  String str = "";
  str += int(val);  //prints the int part
  str += "."; // print the decimal point
  unsigned int frac;
  if(val >= 0) {
    frac = (val - int(val)) * precision;
  }
  else {
    frac = (int(val)- val ) * precision;
  }
  str += int(frac);
  return str;
} 
