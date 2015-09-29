#include "module_handler.h"

void setup() {
  initializeStaticModules();
  initializeDynamicModules();
}

bool once = 1;
void loop() {
  updateIncomingMessage();
  updateStreamMessage();
  if (once) {
    initializeBarebones();
    once = 0;
  }
  updateBarebones();
}
