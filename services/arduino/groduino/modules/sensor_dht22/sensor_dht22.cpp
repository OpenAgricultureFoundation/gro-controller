#include "sensor_dht22.h"

SensorDht22::SensorDht22(uint8_t id, uint8_t pin, String humidity_instruction, String temperature_instruction) {
  id_ = id;
  pin_ = pin;
  humidity_instruction_ = humidity_instruction;
  temperature_instruction_ = temperature_instruction;
  count_ = COUNT;
  first_reading_ = true;
}

void SensorDht22::begin(void) {
  pinMode(pin_, INPUT);
  digitalWrite(pin_, HIGH);
  last_read_time_ = 0;
}

String SensorDht22::get(void) {
  getSensorData();
  String message = "";
  message += "\"" + humidity_instruction_ + "\":{" + id_ + "," + humidity_ + "},";
  message += temperature_instruction_ + "\":{" + id_ + "," + temperature_ + "},";
  return message;
}

bool SensorDht22::set(String instruction) {
  return 0;
}


void SensorDht22::getRawSensorData(void) {
  humidity_raw_ = 0;
  temperature_raw_ = 0;
  if (read()) {
    humidity_raw_ = data[0];
    humidity_raw_ *= 256;
    humidity_raw_ += data[1];
    humidity_raw_ /= 10;
    
    temperature_raw_ = data[2] & 0x7F;
    temperature_raw_ *= 256;
    temperature_raw_ += data[3];
    temperature_raw_ /= 10;
    if (data[2] & 0x80) {
      temperature_raw_ *= -1;
    }    
  }
}

void SensorDht22::getSensorData(void) {
  getRawSensorData();
  filterSensorData();
}

void SensorDht22::filterSensorData(void) {
  humidity_ = humidity_raw_;
  temperature_ = temperature_raw_;
}

boolean SensorDht22::read(void) {
  uint8_t last_state = HIGH;
  uint8_t counter = 0;
  uint8_t j = 0, i;
  unsigned long current_time;

  digitalWrite(pin_, HIGH);
  delay(2); // old delay time was 250

  current_time = millis();
  if (current_time < last_read_time_) {
    // ie there was a rollover
    last_read_time_ = 0;
  }
  if (!first_reading_ && ((current_time - last_read_time_) < 2000)) {
    return true; // return last correct measurement
    // delay(2000 - (currenttime - _lastreadtime));
  }
  first_reading_ = false;
  last_read_time_ = millis();

  data[0] = data[1] = data[2] = data[3] = data[4] = 0;
  
  // now pull it low for ~20 milliseconds
  pinMode(pin_, OUTPUT);
  digitalWrite(pin_, LOW);
  delay(20);
  //cli();
  digitalWrite(pin_, HIGH);
  delayMicroseconds(40);
  pinMode(pin_, INPUT);

  // read in timings
  for ( i=0; i< MAXTIMINGS; i++) {
    counter = 0;
    while (digitalRead(pin_) == last_state) {
      counter++;
      delayMicroseconds(1);
      if (counter == 255) {
        break;
      }
    }
    last_state = digitalRead(pin_);

    if (counter == 255) break;

    // ignore first 3 transitions
    if ((i >= 4) && (i%2 == 0)) {
      // shove each bit into the storage bytes
      data[j/8] <<= 1;
      if (counter > count_)
        data[j/8] |= 1;
      j++;
    }
  }

  // check we read 40 bits and that the checksum matches
  if ((j >= 40) && 
      (data[4] == ((data[0] + data[1] + data[2] + data[3]) & 0xFF)) ) {
    return true;
  }
  return false;
}
  





