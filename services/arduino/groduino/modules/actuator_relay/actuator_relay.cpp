#include "actuator_relay.h"

ActuatorRelay::ActuatorRelay(int id, uint8_t pin, String instruction_code) {
 id_ = id;
 pin_ = pin;
 instruction_code_ = instruction_code;
}

void ActuatorRelay::begin(void) {
 pinMode(pin_,OUTPUT);
 turnOff();
}

String ActuatorRelay::get(void) {
  return ""; //String("\"" + instruction_code_ + "\":" + value_);
}

String ActuatorRelay::set(String message) {
  if (message.substring(0,3) == instruction_code_) {
    struct Instruction instruction;
    String error_message = parseInstruction(message, &instruction);
    if (error_message != "") {
      return error_message;
    }
    if (instruction.value) {
      turnOn();
      return "";
    }
    else {
      turnOff();
      return "";
    }
  }
  return "";
}

String ActuatorRelay::parseInstruction(String message, Instruction *instruction) {
  int len = message.length();
  int first_space = message.indexOf(" ");
  if ((first_space > 0) && (len > first_space)) {
    int second_space = message.indexOf(" ", first_space + 1);
    if ((second_space > 0) && (second_space < len - 1)) {
      // Received good message
      instruction->code = message.substring(0,3);
      instruction->id = (message.substring(first_space, second_space)).toInt();
      instruction->value = (message.substring(second_space, len)).toInt();
      return "";
    }
  }
  String error_message = "\"ERR\":{" + String(1);//error_code_;
  error_message += ",\"Invalid instruction: ";
  error_message += instruction_code_ + " " + id_ + "\"},";
  return error_message;  
}


void ActuatorRelay::turnOn(void){
  digitalWrite(pin_,LOW);
}

void ActuatorRelay::turnOff(void){
  digitalWrite(pin_,HIGH);
}
