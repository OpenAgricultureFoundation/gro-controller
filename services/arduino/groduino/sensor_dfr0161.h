#ifndef SENSOR_DFR0161_H
#define SENSOR_DFR0161_H

#if ARDUINO >= 100
 #include "Arduino.h"
#else
 #include "WProgram.h"
#endif

class SensorDfr0161 {
  public:
    // Public Functions
    SensorDfr0161(uint8_t pin, String instruction_code, int instruction_id_);
    void begin(void);
    String get(void);
    String set(String instruction_code, int instruction_id, String instruction_parameter);

  private:
    // Private Functions
    float getPh(void);
    String floatToString(double val, unsigned int precision);

    //Private Variables
    uint8_t pin_;
    String instruction_code_;
    int instruction_id_;
    float offset_;
    uint8_t number_of_samples_;
};

#endif // SENSOR_DFR0161_H_
