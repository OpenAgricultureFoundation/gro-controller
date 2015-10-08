#include "sensor_dfr0300.h"

//-----------------------------------------------PUBLIC----------------------------------------------//
MovingAverageFilter ec_filter(10);

SensorDfr0300::SensorDfr0300(int temperature_pin, int ec_pin, int ec_enable_pin, String temperature_instruction_code, int temperature_id, String ec_instruction_code, int ec_id) {
  temperature_pin_ = temperature_pin;
  ec_pin_ = ec_pin;
  ec_enable_pin_ = ec_enable_pin;
  temperature_instruction_code_ = temperature_instruction_code;
  temperature_id_ = temperature_id;
  ec_instruction_code_ = ec_instruction_code;
  ec_id_ = ec_id;
}

void SensorDfr0300::begin(void) {
  ds_ = new OneWire(temperature_pin_);
  pinMode(ec_enable_pin_, OUTPUT);
  digitalWrite(ec_enable_pin_, LOW);
  offset_ = 0.15;
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
  message += String(temperature, 1);
  message += ",";

  // Append EC
  message += "\"";
  message += ec_instruction_code_;
  message += " ";
  message += ec_id_;
  message += "\":";
  //message += String(ec,1);
  message += String(ec_avg,1);
  message += ",";

  // Return Message
  return message;
}

String SensorDfr0300::set(String instruction_code, int instruction_id, String instruction_parameter) {
  return "";
}

//-------------------------------------------------PRIVATE-------------------------------------------//
void SensorDfr0300::getSensorData(void) {
  temperature = getTemperature();
  startTempertureConversion();
  ec = getEc(temperature);
  ec_avg = ec_filter.process(ec);
}



float SensorDfr0300::getEc(float temperature_value) { 
  float ec_val;
  int analog_sum = 0;
  const int samples = 20;
  
  for (int i=0; i<samples; i++) {
    analog_sum += analogRead(ec_pin_);
  }
  float analog_avg = (float) analog_sum / samples;
  float analog_voltage = analog_avg*(float)5000/1024;
  float temp_coefficient = 1.0 + 0.0185*(temperature_value - 25.0);
  float coeff_voltage = analog_voltage / temp_coefficient; 
  
  if(coeff_voltage < 0) {
    return 0;
    //Serial.println("No solution!");   //25^C 1413us/cm<-->about 216mv  if the voltage(compensate)<150,that is <1ms/cm,out of the range
  }
  else if (coeff_voltage>3300) {
    return 0;
    //Serial.println("Out of the range!");  //>20ms/cm,out of the range
  }
  else { 
    if(coeff_voltage <= 448) {
      
      return (6.84*coeff_voltage-64.32)/1000 + offset_;   //1ms/cm<EC<=3ms/cm
    }
    else if (coeff_voltage <= 1457) {
      return (6.98*coeff_voltage-127)/1000 + offset_;  //3ms/cm<EC<=10ms/cm
    }
    else {
      return (5.3*coeff_voltage+2278)/1000 + offset_; //10ms/cm<EC<20ms/cm
    }
  }
}

float SensorDfr0300::getTemperature(void) {
  float temp_val;
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
  temp_val = tempRead / 16;

  // Start Conversion For Next Temperature Reading
  startTempertureConversion();

  return temp_val;
}

void SensorDfr0300::startTempertureConversion(void) {
  if ( !ds_->search(addr_)) {
     // Serial.println("no more sensors on chain, reset search!");
      ds_->reset_search();
      return;
  }      
  if ( OneWire::crc8(addr_, 7) != addr_[7]) {
     // Serial.println("CRC is not valid!");
      return;
  }        
  if ( addr_[0] != 0x10 && addr_[0] != 0x28) {
     // Serial.print("Device is not recognized!");
      return;
  }      
  ds_->reset();
  ds_->select(addr_);
  ds_->write(0x44,1); // start conversion, with parasite power on at the end
}

