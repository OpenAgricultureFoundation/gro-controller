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
    SensorDfr0161(uint8_t ph_pin, String ph_instruction_code, int ph_instruction_id);
    void begin(void);
    String get(void);
    String set(String ph_instruction_code, int ph_instruction_id, String pg_instruction_parameter);
    double getPh(void);

    // Public Variables
    float ph;
    
  private:
    // Private Functions
    double avergeArray(int* arr, int number);
    String floatToString(double val, unsigned int precision);

    // Private Variables
    int ph_pin_;
    String ph_instruction_code_;
    int ph_instruction_id_;
    double calibration_coeff_;
    double calibration_offset_;
};

#endif // SENSOR_DFR0161_H_
