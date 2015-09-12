#ifndef GENERAL_CONFIGURATION_H
#define GENERAL_CONFIGURATION_H

#if ARDUINO >= 100
 #include "Arduino.h"
#else
 #include "WProgram.h"
#endif

#include "general_communication.h"

void InitializeConfiguration(void);
void UpdateConfiguration(void);
String HandleIncomingMessage(void);

#endif // GENERAL_CONFIGURATION_H_
