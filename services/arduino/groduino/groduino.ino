#include "module_handler.h"

void setup() {
  initializeStaticModules();
  initializeDynamicModules();
  initializeBarebones();
}

void loop() {
  updateIncomingMessage();
  updateStreamMessage();
  updateBarebones();
}
