#ifndef COMMUNICATION_H
#define COMMUNICATION_H

// msg = {JsonStrings}
// packed_message = SOH msg_size STX msg ETX checksum EOT

#if ARDUINO >= 100
 #include "Arduino.h"
#else
 #include "WProgram.h"
#endif


class Communication {
  public:
    // Public Functions
    Communication(bool external_monitor);
    void begin(void);
    void send(String message);
    bool available(void);
    String receive(void);
    char* floatToString(float value, int places);
    
    // Public Variables
    bool not_connected_;
    bool external_monitor_;

  private:
    // Private Functions
    String getPackedMessage(String message);
    String getChecksum(String message);
    String getUnpackedMessage(String message);
    bool checkStartOfHeader(String message);
    int parseHeader(String message);
    String parseText(String message);
    String parseFooter(String message);
    
    //Private Variables
    uint32_t kBaudRate;
    uint32_t kEstablishConnectionTimeout; // milliseconds
    uint32_t kReceiveTimeout; // milliseconds
    char kStartOfHeaderChar;
    char kStartOfTextChar;
    char kEndOfTextChar;
    char kEndOfTransmissionChar;
    char kEnquireChar;
    char kAcknowledgeChar; 
};

#endif // COMMUNICATION_H_
