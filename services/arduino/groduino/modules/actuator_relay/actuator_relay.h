#ifndef ACTUATOR_RELAY_H
#define ACTUATOR_RELAY_H

#if ARDUINO >= 100
 #include "Arduino.h"
#else
 #include "WProgram.h"
#endif

struct Instruction {
  String code;
  int id;
  int value;
};

class ActuatorRelay {
  public:
    // Public Functions
    ActuatorRelay(int id, uint8_t pin, String instruction_code);
    void begin(void); 
    String get(void); 
    String set(String instruction);
    
  private:
    // Private Functions
    String parseInstruction(String message, Instruction *instruction);
    void turnOn(void);
    void turnOff(void);
    
    // Private Variables
    uint8_t pin_;
    uint8_t id_;
    uint8_t value_;
    String instruction_code_;
};



#endif // ACTUATOR_RELAY_H_

