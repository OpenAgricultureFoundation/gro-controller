#include "sensor_ds1307.h"
#include <Wire.h>

#define DS1307_CTRL_ID 0x68 

// PUBLIC FUNCTIONS
SensorDs1307::SensorDs1307 (int id, String instruction_code) {
  id_ = id;
  instruction_code_ = instruction_code;
}

void SensorDs1307::begin(void) {
  Wire.begin();
}

String SensorDs1307::get(void) {
  String message = "\"" + instruction_code_ + "\":{" + id_ + ",";
  tmElements_t tm;
  if (read(tm)) {
    // Day
    if (tm.Day < 10) {
      message += "0";
    }
    message += tm.Day;
    message += "/";

    // Month
    if (tm.Month < 10) {
      message += "0";
    }
    message += tm.Month;
    message += "/";

    // Year
    message += tmYearToCalendar(tm.Year);
    message += " ";

    // Hour
    if (tm.Hour < 10) {
      message += "0";
    }
    message += tm.Hour;
    message += ":";

    // Minute
    if (tm.Minute < 10) {
      message += "0";
    }
    message += tm.Minute;
    message += ":";

    // Seconds
    if (tm.Second < 10) {
      message += "0";
    }
    message += tm.Second;
    message += "},";
  } 
  else {
    if (chipPresent()) {
        message += "0.0},\"ERR\":{2,\"ds1307\"},";
//      message += "Error: The time is not set on the DS1307 Time Sensor.\n";
//      message += "Likely Cause: The battery became dislodged or died.\n";
//      message += "Possible Fix: Run the set time function.";
    } 
    else {
        message += "0.0},\"ERR\":{3,\"ds1307\"},";
//      message += "Error: Unable to read the time from the DS1307 Time Sensor.\n";
//      message += "Likely Cause: Improper wiring or chip is dead.\n";
//      message += "Possible Fix: Check the circuitry.";
    }
  }
  return message; 
}

bool SensorDs1307::set(String instruction) {
  return 0;
}

String SensorDs1307::setTime(void) {
  String message = "";
  tmElements_t tm;
  bool parse=false;
  bool config=false;

  // get the date and time the compiler was run
  if (getDate(__DATE__, &tm) && getTime(__TIME__, &tm)) {
    parse = true;
    // and configure the RTC with this info
    if (write(tm)) {
      config = true;
    }
  }

  if (parse && config) {
    message += "SensorDs1307 configured. Time =";
    message += __TIME__;
    message += ", Date =";
    message += __DATE__;
  } else if (parse) {
    message += "Error: SensorDs1307 communication error.";
    message += "Details: Please check your circuitry.";
  } else {
    message += "Could not parse info from the compiler, Time =\"";
    message += __TIME__;
    message += "\", Date =\"";
    message += __DATE__;
    message += "\"";
  }
  
}
 

// PRIVATE FUNCTIONS
bool SensorDs1307::getTime(const char *str, tmElements_t *tm)
{
  int Hour, Min, Sec;

  if (sscanf(str, "%d:%d:%d", &Hour, &Min, &Sec) != 3) return false;
  tm->Hour = Hour;
  tm->Minute = Min;
  tm->Second = Sec;
  return true;
}

bool SensorDs1307::getDate(const char *str, tmElements_t *tm) {
  const char *monthName[12] = {
    "Jan", "Feb", "Mar", "Apr", "May", "Jun",
    "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"
  };
  
  char Month[12];
  int Day, Year;
  uint8_t monthIndex;

  if (sscanf(str, "%s %d %d", Month, &Day, &Year) != 3) return false;
  for (monthIndex = 0; monthIndex < 12; monthIndex++) {
    if (strcmp(Month, monthName[monthIndex]) == 0) break;
  }
  if (monthIndex >= 12) return false;
  tm->Day = Day;
  tm->Month = monthIndex + 1;
  tm->Year = CalendarYrToTm(Year);
  return true;
}

// Function: Get current time
time_t SensorDs1307::getData()   // Aquire data from buffer and convert to time_t
{
  tmElements_t tm;
  if (read(tm) == false) return 0;
  return(makeTime(tm));
}

// Funtion: Set current time
bool SensorDs1307::setData(time_t t)
{
  tmElements_t tm;
  breakTime(t, tm);
  tm.Second |= 0x80;  // stop the clock 
  write(tm); 
  tm.Second &= 0x7f;  // start the clock
  write(tm); 
}

// Aquire data from the RTC chip in BCD format
bool SensorDs1307::read(tmElements_t &tm)
{
  uint8_t sec;
  Wire.beginTransmission(DS1307_CTRL_ID);
#if ARDUINO >= 100  
  Wire.write((uint8_t)0x00); 
#else
  Wire.send(0x00);
#endif  
  if (Wire.endTransmission() != 0) {
    exists = false;
    return false;
  }
  exists = true;

  // request the 7 data fields   (secs, min, hr, dow, date, mth, yr)
  Wire.requestFrom(DS1307_CTRL_ID, tmNbrFields);
  if (Wire.available() < tmNbrFields) return false;
#if ARDUINO >= 100
  sec = Wire.read();
  tm.Second = bcd2dec(sec & 0x7f);   
  tm.Minute = bcd2dec(Wire.read() );
  tm.Hour =   bcd2dec(Wire.read() & 0x3f);  // mask assumes 24hr clock
  tm.Wday = bcd2dec(Wire.read() );
  tm.Day = bcd2dec(Wire.read() );
  tm.Month = bcd2dec(Wire.read() );
  tm.Year = y2kYearToTm((bcd2dec(Wire.read())));
#else
  sec = Wire.receive();
  tm.Second = bcd2dec(sec & 0x7f);   
  tm.Minute = bcd2dec(Wire.receive() );
  tm.Hour =   bcd2dec(Wire.receive() & 0x3f);  // mask assumes 24hr clock
  tm.Wday = bcd2dec(Wire.receive() );
  tm.Day = bcd2dec(Wire.receive() );
  tm.Month = bcd2dec(Wire.receive() );
  tm.Year = y2kYearToTm((bcd2dec(Wire.receive())));
#endif
  if (sec & 0x80) return false; // clock is halted
  return true;
}

bool SensorDs1307::write(tmElements_t &tm)
{
  Wire.beginTransmission(DS1307_CTRL_ID);
#if ARDUINO >= 100  
  Wire.write((uint8_t)0x00); // reset register pointer  
  Wire.write(dec2bcd(tm.Second)) ;   
  Wire.write(dec2bcd(tm.Minute));
  Wire.write(dec2bcd(tm.Hour));      // sets 24 hour format
  Wire.write(dec2bcd(tm.Wday));   
  Wire.write(dec2bcd(tm.Day));
  Wire.write(dec2bcd(tm.Month));
  Wire.write(dec2bcd(tmYearToY2k(tm.Year))); 
#else  
  Wire.send(0x00); // reset register pointer  
  Wire.send(dec2bcd(tm.Second)) ;   
  Wire.send(dec2bcd(tm.Minute));
  Wire.send(dec2bcd(tm.Hour));      // sets 24 hour format
  Wire.send(dec2bcd(tm.Wday));   
  Wire.send(dec2bcd(tm.Day));
  Wire.send(dec2bcd(tm.Month));
  Wire.send(dec2bcd(tmYearToY2k(tm.Year)));   
#endif
  if (Wire.endTransmission() != 0) {
    exists = false;
    return false;
  }
  exists = true;
  return true;
}

// Convert Decimal to Binary Coded Decimal (BCD)
uint8_t SensorDs1307::dec2bcd(uint8_t num)
{
  return ((num/10 * 16) + (num % 10));
}

// Convert Binary Coded Decimal (BCD) to Decimal
uint8_t SensorDs1307::bcd2dec(uint8_t num)
{
  return ((num/16 * 10) + (num % 16));
}

// Function: Print to Digits
void SensorDs1307::print2digits(int number) {
  if (number >= 0 && number < 10) {
    Serial.write('0');
  }
  Serial.print(number);
}


bool SensorDs1307::exists = false;
