// http://www.dfrobot.com/index.php?route=product/product&product_id=879#.Va0RhxNViko

#ifndef SENSOR_DS1307_H
#define SENSOR_DS1307_H

#if ARDUINO >= 100
 #include "Arduino.h"
#else
 #include "WProgram.h"
#endif

#include "support_time.h"

class SensorDs1307 {
  public:
  // Public Functions
  SensorDs1307 (int id, String instruction_code);
  void begin(void);
  String get(void);
  bool set(String instruction);

  // This needs to be removed
  String setTime(void);

  private:
  // Private Functions
  static time_t getData();
  static bool setData(time_t t);
  static bool read(tmElements_t &tm);
  static bool write(tmElements_t &tm);
  static bool chipPresent() { return exists; }
  static uint8_t dec2bcd(uint8_t num);
  static uint8_t bcd2dec(uint8_t num);
  void print2digits(int number);
  bool getDate(const char *str, tmElements_t *tm);
  bool getTime(const char *str, tmElements_t *tm);

  // Private Variables
  static bool exists;
  int id_;
  uint32_t start_time_;
  String instruction_code_;
};

#endif // SENSOR_DS1307_H_
