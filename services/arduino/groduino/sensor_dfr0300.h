// http://www.dfrobot.com/wiki/index.php/Analog_EC_Meter_SKU:DFR0300

#ifndef SENSOR_DFR0300_H
#define SENSOR_DFR0300_H

#if ARDUINO >= 100
 #include "Arduino.h"
#else
 #include "WProgram.h"
#endif

#include "support_one_wire.h"

class SensorDfr0300 {
  public:
    // Public Functions
    //SensorDfr0300(int temperature_pin, int ec_pin, String temperature_instruction_code, int temperature_id, String ec_instruction_code, int ec_id, OneWire *ds); 
    SensorDfr0300(int temperature_pin, int ec_pin, int ec_enable_pin, String temperature_instruction_code, int temperature_id, String ec_instruction_code, int ec_id); 
    void begin(void);
    String get(void);
    String set(String instruction_code, int instruction_id, String instruction_parameter);

    // Public Variables
    float temperature_; //degrees C
    float ec_; //uS/cm

  private:
    // Private Functions
    void getSensorData(void);   
    void getTemperature(void);
    void startTempertureConversion(void);
    void getEc(float temperature);
    String floatToString(double val, unsigned int precision);
    
    float TempProcess(bool ch);
//    
  
    // Private Variables
    int temperature_pin_;
    int ec_pin_;
    String temperature_instruction_code_;
    int temperature_id_;
    String ec_instruction_code_;
    int ec_id_;
    float ec_coefficient_;
    float ec_offset_;
    int ec_enable_pin_;
    
    byte data_[12];
    byte addr_[8];

    OneWire *ds_;
};

#endif // SENSOR_DFR0300_H_
