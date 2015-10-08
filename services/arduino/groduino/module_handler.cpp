#include "module_handler.h"

// Declare Communication Object
Communication communication(0); // 1 to listen

// Function(initializeStaticModules): called once to initialize all static modules
void initializeStaticModules(void) {
  communication.begin();
}

// Function(updateIncomingMessage): if new message is available, receive message and pass to
// handler function. If handler function returns response message, send out
void updateIncomingMessage(void) {
  // Check for Message(s) And Handle If Necessary
  String response_message = "";
  while (communication.available()) { // read in message(s) until nothing in serial buffer
    response_message += handleIncomingMessage();
  }
  // Append Responses From Message(s) Then Send
  if (response_message != "") {
    response_message = "\"GTYP\":\"Response\"," + response_message;
    response_message += "\"GEND\":0";
    communication.send(response_message);
  }
}

// Function(parseIncomingMessage): breaks incoming message into 3 parts: Instruction Code,
// Instruction ID, Instruction Parameter then returns the parts as an Instruction Object
// Also, the Instruction Valid parameter is set accordingly.
Instruction parseIncomingMessage(String message) {
  // Initialize Instruction
  Instruction instruction;
  instruction.valid = 0;

  // Get Instruction Data
  int len = message.length();
  int first_space = message.indexOf(" ");
  if ((first_space > 0) && (len > first_space)) {
    int second_space = message.indexOf(" ", first_space + 1);
    if ((second_space > 0) && (second_space < len - 1)) {
      // Received good message
      instruction.code = message.substring(0, 4);
      instruction.id = (message.substring(first_space, second_space)).toInt();
      instruction.parameter = message.substring(second_space + 1, len);
      instruction.valid = 1;
    }
  }

  // Return Instruction Data
  return instruction;
}

//---------------------------------------DYNAMIC MODULE HANDLER CODE---------------------------------//
// Import Module Libraries
#include "sensor_tsl2561.h"
#include "sensor_dht22.h"
#include "sensor_gc0011.h"
#include "sensor_dfr0161.h"
#include "actuator_relay.h"
#include "sensor_dfr0300.h"
#include "sensor_contact_switch.h"
#include "rgb_lcd.h"

// Electronics Panel Iteration2
SensorTsl2561 sensor_tsl2561_light_intensity_default("SLIN", 1, "SLPA", 1);
SensorDht22 sensor_dht22_air_temperature_humidity_default(A0, "SATM", 1, "SAHU", 1);
SensorGc0011 sensor_gc0011_air_co2_temperature_humidity_default(12, 11, "SACO", 1, "SATM", 2, "SAHU", 2);
SensorDfr0161 sensor_dfr0161_water_ph_default(A1, "SWPH", 1);
SensorDfr0300 sensor_dfr0300_water_temperature_ec_default(5, A2, 2, "SWTM", 1, "SWEC", 1);
SensorContactSwitch sensor_contact_switch_general_shell_open_default(4, "SGSO", 1);
SensorContactSwitch sensor_contact_switch_general_window_open_default(3, "SGWO", 1);

// AC Relay Block: AC[1:4] <--> Pin[9:6]
// pin 6 --> port 4
ActuatorRelay actuator_relay_air_heater_default(6, "AAHE", 1); // AC port 4
ActuatorRelay actuator_relay_light_panel_default(8, "ALPN", 1); // AC port 2
ActuatorRelay actuator_relay_air_humidifier_default(9, "AAHU", 1); // AC port 1

// DC Relay Block
ActuatorRelay actuator_relay_air_vent_default(14, "AAVE", 1);
ActuatorRelay actuator_relay_air_circulation_default(15, "AACR", 1);
ActuatorRelay actuator_relay_light_chamber_illumination_default(53, "ALPN", 2);  // ALCI
ActuatorRelay actuator_relay_light_motherboard_illumination_default(52, "ALMI", 1);

// Barebones Swank
rgb_lcd lcd;

// Function(initializeDynamicModules): called once to initialize all dynamic modules
void initializeDynamicModules(void) {
  sensor_tsl2561_light_intensity_default.begin();
  sensor_dht22_air_temperature_humidity_default.begin();
  sensor_gc0011_air_co2_temperature_humidity_default.begin();
  sensor_dfr0161_water_ph_default.begin();
  sensor_dfr0300_water_temperature_ec_default.begin();
  sensor_contact_switch_general_shell_open_default.begin();
  sensor_contact_switch_general_window_open_default.begin();
  actuator_relay_air_heater_default.begin();
  actuator_relay_air_humidifier_default.begin();
  actuator_relay_air_vent_default.begin();
  actuator_relay_air_circulation_default.begin();
  actuator_relay_light_panel_default.begin();
  actuator_relay_light_chamber_illumination_default.begin();
  actuator_relay_light_motherboard_illumination_default.begin();

  // Set Default States
  actuator_relay_air_circulation_default.set("AACR", 1, "1");
  actuator_relay_light_motherboard_illumination_default.set("ALMI", 1, "1");
  actuator_relay_air_vent_default.set("AAVE", 1, "1");
}


// Function(updateStreamMessage):  polls all objects and appends to message stream
// note: all apended data must be in JSON format
void updateStreamMessage(void) {
  // Initialize Stream Message
  String stream_message = "\"GTYP\":\"Stream\",";

  // Get Stream Message
  stream_message += sensor_dfr0300_water_temperature_ec_default.get();
  stream_message += sensor_tsl2561_light_intensity_default.get();
  stream_message += sensor_dht22_air_temperature_humidity_default.get(); // does not work on 1.0
  stream_message += sensor_gc0011_air_co2_temperature_humidity_default.get();
  stream_message += sensor_dfr0161_water_ph_default.get();
  stream_message += sensor_contact_switch_general_shell_open_default.get();
  stream_message += sensor_contact_switch_general_window_open_default.get();
  stream_message += sensor_dfr0161_water_ph_default.get();
  stream_message += actuator_relay_air_heater_default.get();
  stream_message += actuator_relay_air_humidifier_default.get();
  stream_message += actuator_relay_air_vent_default.get();
  stream_message += actuator_relay_air_circulation_default.get();
  stream_message += actuator_relay_light_panel_default.get();
  stream_message += actuator_relay_light_chamber_illumination_default.get();
  stream_message += actuator_relay_light_motherboard_illumination_default.get();

  // Return Stream Message
  stream_message += "\"GEND\":0";

  // Send Stream Message
  communication.send(stream_message);
}

// Function (handleIncomingMessage): incoming messages get passed into this function. Messages are
// parsed into 3 main components: Instruction Code, Instruction ID, Instruction Parameter.
// These components are passed piecewise into all <module>.set functions. If a return message is
// geneated from the <module>.set function, this function will return that message
String handleIncomingMessage(void) {
  // Parse Message into: Code - ID - Parameter
  String return_message = "";
  String incoming_message = communication.receive();
  Instruction instruction = parseIncomingMessage(incoming_message);

  // Pass Parsed Message To All Objects and Update Return Message if Applicable
  if (instruction.valid) {
    return_message += sensor_tsl2561_light_intensity_default.set(instruction.code, instruction.id, instruction.parameter);
    return_message += sensor_dht22_air_temperature_humidity_default.set(instruction.code, instruction.id, instruction.parameter);
    return_message += sensor_gc0011_air_co2_temperature_humidity_default.set(instruction.code, instruction.id, instruction.parameter);
    return_message += sensor_dfr0300_water_temperature_ec_default.set(instruction.code, instruction.id, instruction.parameter);
    return_message += sensor_dfr0161_water_ph_default.set(instruction.code, instruction.id, instruction.parameter);
    return_message += sensor_contact_switch_general_shell_open_default.set(instruction.code, instruction.id, instruction.parameter);
    return_message += sensor_contact_switch_general_window_open_default.set(instruction.code, instruction.id, instruction.parameter);
    return_message += actuator_relay_air_heater_default.set(instruction.code, instruction.id, instruction.parameter);
    return_message += actuator_relay_air_humidifier_default.set(instruction.code, instruction.id, instruction.parameter);
    return_message += actuator_relay_air_vent_default.set(instruction.code, instruction.id, instruction.parameter);
    return_message += actuator_relay_air_circulation_default.set(instruction.code, instruction.id, instruction.parameter);
    return_message += actuator_relay_light_panel_default.set(instruction.code, instruction.id, instruction.parameter);
    return_message += actuator_relay_light_chamber_illumination_default.set(instruction.code, instruction.id, instruction.parameter);
    return_message += actuator_relay_light_motherboard_illumination_default.set(instruction.code, instruction.id, instruction.parameter);
  }
  return return_message;
}

// This is a stripped version of a food computer setup. Intent is that it can keep a system functional
// while networks are being setup && configured. super hack.
uint32_t start_time;
const uint32_t hour = 3600000; //milliseconds
int ec_ph_sw_pin = 2;
void initializeBarebones(void) {
  // Barebones swank
  lcd.begin(16, 2);
  lcd.setRGB(0, 255, 0);
  lcd.setCursor(0, 0);
  lcd.write("EC:0.0");
  lcd.setCursor(0, 1);
  lcd.write("pH:0.0");
  //  lcd.setCursor(9,1);
  //  lcd.write("RH:0.0");
  //  lcd.setCursor(8,0);
  //  lcd.write("CO2:0.0");
  pinMode(ec_ph_sw_pin, INPUT_PULLUP);
  start_time = millis(); // should really be RTC, or at least EEPROM. aint nobody got time for that though
}

void updateBarebones(void) {
  updateLcdSwitched();
  // Cycle Resetter
  if (millis() - start_time > 24 * hour) {
    start_time = millis();
  }
  // Grow Light ON Cycle
  if ((millis() - start_time < 18 * hour) && (actuator_relay_light_panel_default.value_ != 1)) {
    actuator_relay_light_panel_default.set("ALPN", 1, "1");
  }

  // Grow Light OFF Cycle
  if ((millis() - start_time > 18 * hour) && (actuator_relay_light_panel_default.value_ != 0)) {
    actuator_relay_light_panel_default.set("ALPN", 1, "0");
  }
}

// Function makes nice things on LCD
// Also some function prep........
// EC init
float prev_ec = 0;
int prev_ec_len = 3;
bool ec_prev_disp = false;
// awesome playground: 2.3-2.7
// dearborne, lincoln, film: 1.8-2.2
float min_ec = 1.8; 
float max_ec = 2.2;
// pH init
float prev_ph = 0;
int prev_ph_len = 3;
bool ph_prev_disp = false;
float min_ph = 5.5;
float max_ph = 6.5;
// CO2 init
float prev_co2 = 0.0;
int prev_co2_len = 3;
// RH init
float prev_rh = 0.0;
int prev_rh_len = 3;

//void updateLcd(void) {
//  // Update EC
//  lcd.setCursor(0, 0);
//  lcd.write("EC:");
//  float ec = sensor_dfr0300_water_temperature_ec_default.ec;
//  if (ec != prev_ec) {
//    // Erase
//    lcd.setCursor(3, 0);
//    for (int i = 0; i < prev_ec_len; i++) {
//      lcd.print(" ");
//    }
//    // Rewrite
//    lcd.setCursor(3, 0);
//    String msg = String(ec, 1);
//    lcd.print(msg);
//    prev_ec = ec;
//    prev_ec_len = msg.length();
//  }
//
//  // Update pH
//  float ph = sensor_dfr0161_water_ph_default.ph_avg;
//  if (ph != prev_ec) {
//    // Erase
//    lcd.setCursor(3, 1);
//    for (int i = 0; i < prev_ph_len; i++) {
//      lcd.print(" ");
//    }
//    // Rewrite
//    lcd.setCursor(3, 1);
//    String msg = String(ph, 1);
//    lcd.print(msg);
//    prev_ph = ph;
//    prev_ph_len = msg.length();
//  }
//}


void updateLcdSwitched(void) {
  if (digitalRead(ec_ph_sw_pin) == HIGH) { // Handle EC Display
    // Get EC
    float ec_raw = sensor_dfr0300_water_temperature_ec_default.ec_avg;
    float ec = round(ec_raw*10)/(float)10;

    // Update Display
    lcd.clear();
    lcd.print("EC: " + String(ec,1));
  }
  else {
    // Get PH
    float ph_raw = sensor_dfr0161_water_ph_default.ph_avg;
    float ph = round(ph_raw*10)/(float)10;

    // Update Display
    lcd.clear();
    lcd.print("PH: " + String(ph,1));
  }
}
    
    
//    // Update If New EC Value OR Not Previously Displayed
//    if ((prev_ec != ec) || (ec_prev_disp == false)) {
//      // Display Value
//      lcd.clear();
//      lcd.print("EC: " + String(ec));
//
//      // Display Backlight
//      if ((ec > min_ec) && (ec < max_ec)) {
//        lcd.setRGB(0, 255, 0);
//      }
//      else {
//        lcd.setRGB(255, 0, 0);
//      }
//
//      // Update Previous Display State
//      ec_prev_disp = true;
//      ph_prev_disp = false;
//    }
//  }
  
//  else { // Handle PH Display
//    // Update pH
//    float ph = sensor_dfr0161_water_ph_default.ph_avg;
//    if (ph != prev_ec) {
//      // Erase
//      lcd.clear();
//      lcd.setCursor(0, 0);
//      lcd.write("PH:");
//      lcd.setCursor(3, 0);
//      for (int i = 0; i < prev_ph_len; i++) {
//        lcd.print(" ");
//      }
//      // Rewrite
//      lcd.setCursor(3, 0);
//      String msg = String(ph, 1);
//      lcd.print(msg);
//      prev_ph = ph;
//      prev_ph_len = msg.length();
//
//
//      // Update LCD Mood
//      if ((ph > min_ph) && (ph < max_ph)) {
//        lcd.setRGB(0, 255, 0);
//      }
//      else {
//        lcd.setRGB(255, 0, 0);
//      }
//    }
//  }
// }




