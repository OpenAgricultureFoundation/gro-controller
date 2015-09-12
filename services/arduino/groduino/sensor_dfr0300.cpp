#include "sensor_dfr0300.h"

//-----------------------------------------------PUBLIC----------------------------------------------//

SensorDfr0300::SensorDfr0300(int temperature_pin, int ec_pin, String temperature_instruction_code, int temperature_id, String ec_instruction_code, int ec_id) {
  temperature_pin_ = temperature_pin;
  ec_pin_ = ec_pin;
  temperature_instruction_code_ = temperature_instruction_code;
  temperature_id_ = temperature_id;
  ec_instruction_code_ = ec_instruction_code;
  ec_id_ = ec_id;
}

void SensorDfr0300::begin(void) {
  ds_ = new OneWire(temperature_pin_);
}

String SensorDfr0300::get(void) {
  // Get Temperature and EC Data
  getSensorData();

  // Initialize Message
  String message = "";

  // Append Temperature
  message += "\"";
  message += temperature_instruction_code_;
  message += " ";
  message += temperature_id_;
  message += "\":";
  message += floatToString(temperature_, 100);
  message += ",";

  // Append EC
  message += "\"";
  message += ec_instruction_code_;
  message += " ";
  message += ec_id_;
  message += "\":";
  message += floatToString(ec_, 100);
  message += ",";

  // Return Message
  return message;
}

String SensorDfr0300::set(String instruction_code, int instruction_id, String instruction_parameter) {
  return "";
}

//-------------------------------------------------PRIVATE-------------------------------------------//
void SensorDfr0300::getSensorData(void) {
  getTemperature();
  startTempertureConversion();
  getEc(temperature_);
}

void SensorDfr0300::getEc(float temperature) { 
  float analog;
  int i;
  for (i=0; i<20; i++) {
    analog += analogRead(ec_pin_);
  }
  analog /= 20;
  
  float voltage = analog*(float)5000/1024;
  float temp_coefficient = 1.0 + 0.0185*(temperature - 25.0);
  float coefficient_voltage = (float)voltage/temp_coefficient;  
  if(coefficient_voltage<150) {
    // Error
    ec_ = 0.0;
    //Serial.println("No solution!");   //25^C 1413us/cm<-->about 216mv  if the voltage(compensate)<150,that is <1ms/cm,out of the range
  }
  else if (coefficient_voltage>3300) {
    // Error
    ec_ = 0.0;
    //Serial.println("Out of the range!");  //>20ms/cm,out of the range
  }
  else { 
    if(coefficient_voltage<=448) {
      ec_ = 6.84*coefficient_voltage-64.32;   //1ms/cm<EC<=3ms/cm
    }
    else if (coefficient_voltage<=1457) {
      ec_ = 6.98*coefficient_voltage-127;  //3ms/cm<EC<=10ms/cm
    }
    else {
      ec_ = 5.3*coefficient_voltage+2278; //10ms/cm<EC<20ms/cm
    }
    ec_ /= 1000;    //convert us/cm to ms/cm
  }
}

void SensorDfr0300::getTemperature(void) {
  // Read Temperature
  byte present = ds_->reset();
  ds_->select(addr_);    
  ds_->write(0xBE); // Read Scratchpad            
  for (int i = 0; i < 9; i++) { // we need 9 bytes
    data_[i] = ds_->read();
  }         
  ds_->reset_search();           
  byte MSB = data_[1];
  byte LSB = data_[0];        
  float tempRead = ((MSB << 8) | LSB); //using two's compliment
  temperature_ = tempRead / 16;

  // Start Conversion For Next Temperature Reading
  startTempertureConversion();
}

void SensorDfr0300::startTempertureConversion(void) {
  if ( !ds_->search(addr_)) {
     // Serial.println("no more sensors on chain, reset search!");
      ds_->reset_search();
      return;
  }      
  if ( OneWire::crc8(addr_, 7) != addr_[7]) {
      // Error
     // Serial.println("CRC is not valid!");
      return;
  }        
  if ( addr_[0] != 0x10 && addr_[0] != 0x28) {
      // Error
     // Serial.print("Device is not recognized!");
      return;
  }      
  ds_->reset();
  ds_->select(addr_);
  ds_->write(0x44,1); // start conversion, with parasite power on at the end
}

String SensorDfr0300::floatToString(double val, unsigned int precision) {
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

