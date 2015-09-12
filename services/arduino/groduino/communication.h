#ifndef GENERAL_COMMUNICATION_H
#define GENERAL_COMMUNICATION_H

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
    void begin(void);
    void send(String message);
    bool available(void);
    String receive(void);
    
    // Public Variables
    bool not_connected_ = 0;

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
    const uint32_t kBaudRate = 9600;
    const uint32_t kEstablishConnectionTimeout = 2000; // milliseconds
    const uint32_t kReceiveTimeout = 2000; // milliseconds
    const char kStartOfHeaderChar = 1;
    const char kStartOfTextChar = 2;
    const char kEndOfTextChar = 3;
    const char kEndOfTransmissionChar = 4;
    const char kEnquireChar = 5;
    const char kAcknowledgeChar = 6; 
};

#endif // GENERAL_COMMUNICATION_H_
