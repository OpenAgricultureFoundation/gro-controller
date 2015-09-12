#include "module_handler.h"

void setup() {
  initializeStaticModules();
  initializeDynamicModules();
}

void loop() {
  updateIncomingMessage();
  updateStreamMessage();
}