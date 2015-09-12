#include "general_configuration.h"

// Really want to remove this jank...
#include <Wire.h>
#include <SoftwareSerial.h>

void setup() {
  InitializeConfiguration();
}

void loop() {
  UpdateConfiguration();
}
