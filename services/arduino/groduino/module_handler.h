#ifndef MODULE_HANDLER_H
#define MODULE_HANDLER_H

#if ARDUINO >= 100
 #include "Arduino.h"
#else
 #include "WProgram.h"
#endif

#include "communication.h"

//------------------------------------------------PUBLIC---------------------------------------------//
void initializeStaticModules(void);
void initializeDynamicModules(void);
void updateIncomingMessage(void);
void updateStreamMessage(void);
void initializeBarebones(void);
void updateBarebones(void);

//------------------------------------------------PRIVATE--------------------------------------------//
void updateLcd(void);
void updateLcdSwitched(void);

struct Instruction {
  String code;
  int id;
  String parameter;
  bool valid;
};

String handleIncomingMessage(void);
Instruction parseIncomingMessage(String message);

#endif // MODULE_HANDLER_H_
