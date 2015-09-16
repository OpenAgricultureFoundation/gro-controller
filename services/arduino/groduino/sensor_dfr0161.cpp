#include "sensor_dfr0161.h"

//------------------------------------------PUBLIC FUNCTIONS----------------------------------------//
SensorDfr0161::SensorDfr0161(uint8_t ph_pin, String ph_instruction_code, int ph_instruction_id) {
  ph_instruction_id_ = ph_instruction_id;
  ph_pin_ = ph_pin;
  ph_instruction_code_ = ph_instruction_code;
}

void SensorDfr0161::begin(void) {
  calibration_coeff_ = 3.5;
  calibration_offset_ = -0.1;
}

String SensorDfr0161::get(void) {
  // Initialize Message
  String message = "\"";

  // Get Data For pH
  ph = getPh();

  // Append pH
  message += ph_instruction_code_;
  message += " ";
  message += ph_instruction_id_;
  message += "\":";
  message += String(ph,1);
  message += ",";

  // Return Message
  return message;
}

String SensorDfr0161::set(String ph_instruction_code, int ph_instruction_id, String ph_instruction_parameter) {
  return "";
}

//-----------------------------------------PRIVATE FUNCTIONS---------------------------------------//
double SensorDfr0161::getPh(void) {
  // Sampling Specifications
  int samples = 40;
  int voltage[samples];
  const int sample_time_delta = 20; //milliseconds

  // Acquire Samples
  for (int i=0; i<samples; i++) {
    voltage[i] = analogRead(ph_pin_);
  }

  // Remove Min & Max Samples, Then Average
  double volts = avergeArray(voltage, samples)*5.0/1024;

  // Convert Average Voltage to pH
  return calibration_coeff_*volts + calibration_offset_;;
}

double SensorDfr0161::avergeArray(int* arr, int number){
  int i;
  int max,min;
  double avg;
  long amount=0;
  if(number<=0){
    Serial.println("Error number for the array to averaging!/n");
    return 0;
  }
  if(number<5){   //less than 5, calculated directly statistics
    for(i=0;i<number;i++){
      amount+=arr[i];
    }
    avg = amount/number;
    return avg;
  }else{
    if(arr[0]<arr[1]){
      min = arr[0];max=arr[1];
    }
    else{
      min=arr[1];max=arr[0];
    }
    for(i=2;i<number;i++){
      if(arr[i]<min){
        amount+=min;        //arr<min
        min=arr[i];
      }else {
        if(arr[i]>max){
          amount+=max;    //arr>max
          max=arr[i];
        }else{
          amount+=arr[i]; //min<=arr<=max
        }
      }//if
    }//for
    avg = (double)amount/(number-2);
  }//if
  return avg;
}

String SensorDfr0161::floatToString(double val, unsigned int precision) {
// prints val with number of decimal places determine by precision
// NOTE: precision is 1 followed by the number of zeros for the desired number of decimial places
// example: printDouble( 3.1415, 100); // prints 3.14 (two decimal places)
  String str = "";
  str += int(val);  //prints the int part
  str += "."; // print the decimal point
  unsigned int frac;
  if(val >= 0) {
    frac = (val - int(val)) * precision;
  }
  else {
    frac = (int(val)- val ) * precision;
  }
  str += int(frac);
  return str;
} 

