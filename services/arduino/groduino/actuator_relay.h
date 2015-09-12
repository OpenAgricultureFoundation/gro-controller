#ifndef ACTUATOR_RELAY_H
#define ACTUATOR_RELAY_H

#if ARDUINO >= 100
 #include "Arduino.h"
#else
 #include "WProgram.h"
#endif

class ActuatorRelay {
  public:
    // Public Functions
    ActuatorRelay(int pin, String instruction_code, int instruction_id);
    void begin(void); 
    String get(void); 
    String set(String instruction_code, int instruction_id, String instruction_parameter);

    // Public Variables
    int value_;
    
  private:
    // Private Functions
    void turnOn(void);
    void turnOff(void);
    
    // Private Variables
    int pin_;
    int instruction_id_;
    String instruction_code_;
};

#endif // ACTUATOR_RELAY_H_
