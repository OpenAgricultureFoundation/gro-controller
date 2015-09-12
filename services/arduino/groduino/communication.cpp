#include "communication.h"

Communication::Communication(bool external_monitor) {
  external_monitor_ = external_monitor;
}

void Communication::begin(void) {
  kBaudRate = 9600;
  kEstablishConnectionTimeout = 2000; // milliseconds
  kReceiveTimeout = 5000; // milliseconds
  kStartOfHeaderChar = 1;
  kStartOfTextChar = 2;
  kEndOfTextChar = 3;
  kEndOfTransmissionChar = 4;
  kEnquireChar = 5;
  kAcknowledgeChar = 6; 
  if (external_monitor_) {
    Serial1.begin(kBaudRate);
    Serial1.println("External monitor begin...");
  }
  
  Serial.begin(kBaudRate);
  Serial.write(kEnquireChar);  // send enquiry
  uint32_t start_time = millis();
  while (1) {
    if (Serial.available()) { 
      if (Serial.read() == kAcknowledgeChar) { // await acknowledgement
        Serial.write(kAcknowledgeChar); // acknowledge acknowledgementq
        not_connected_ = 0;
        if (external_monitor_) {
          Serial1.println("Connected to rPi!");
        }
        return; // connected!
      }
    }
    if (millis() - start_time > kEstablishConnectionTimeout) {
      String connection_error_message = "Did not establish connection with rPi";
      if (external_monitor_) {
        Serial1.println(connection_error_message);
      }
      Serial.println(connection_error_message);
      not_connected_ = 1;
      break; // timed out :(
    }
  }
}

void Communication::send(String outgoing_message) {
  outgoing_message = "{" + outgoing_message + "},";
  
  if (not_connected_) {
    if (external_monitor_) {
      Serial1.println("Sending Unpacked>>> " + outgoing_message);
    }
    Serial.println(outgoing_message);
  }
  else { // Connected to rPi
    String packed_message = getPackedMessage(outgoing_message);
    if (external_monitor_) {
      Serial1.println("Sending Packed>>> " + packed_message);
    }
    Serial.print(packed_message);
  }
}

bool Communication::available(void) {
  if (Serial.available()) {
    return 1;
  }
  else if (external_monitor_ && Serial1.available()) {
    return 1;
  }
  else {
    return 0;
  }
}

String Communication::receive(void) { 
  String incoming_message = "";
  char incoming_char;
  bool timed_out = 0;
  uint32_t start_time = millis();
  
  // Handle External Monitor Receive Message
  if (external_monitor_ && Serial1.available()) {
    while (1) {
      // Read in New Serial Data
      delay(10);
      incoming_char = Serial1.read();

      // Check for Break Conditions and Append Char to Message
      if (incoming_char == '\n') {
        break;
      }
      
      incoming_message += incoming_char;
     
      if (millis() - start_time > kReceiveTimeout) {
        timed_out = 1;
        break;
      }
    }

    // Return if Message Not Null
    if (incoming_message != "") {
      Serial1.print("Received@External>>> ");
      Serial1.println(incoming_message);
      return incoming_message;
    }
    
  }

  // Handle Other Messages
  while (1) {
    delay(10);
    incoming_char = Serial.read();

    if (not_connected_ && (incoming_char == '\n')) {
      break;
    }
    if (!not_connected_ && (incoming_char == kEndOfTransmissionChar)) {
      break;
    }
    
    incoming_message += incoming_char;
    
    if (millis() - start_time > kReceiveTimeout) {
      timed_out = 1;
      break;
    }
  }
  if (not_connected_) {
    if (timed_out) {
      incoming_message = "Timed Out";
    }
    if (external_monitor_) {
      Serial1.print("Received@Groterm>>> "); 
      Serial1.println(incoming_message);
    }
    return incoming_message;
  }
  else {
    if (timed_out) {
      if (external_monitor_) {
        Serial1.print("Received@Daemon>>> Timed out. Message received: ");
        Serial1.println(incoming_message);
      }
      return "";
    } 
    String unpacked_message =  getUnpackedMessage(incoming_message);
    if (external_monitor_) {
      Serial1.println("Received@Daemon>>> " + unpacked_message); 
    }
    return unpacked_message;
  }
}

String Communication::getPackedMessage(String message) {
  String packed_message = "";
  String checksum = getChecksum(message);
  packed_message += kStartOfHeaderChar; 
  packed_message += message.length();
  packed_message += kStartOfTextChar; 
  packed_message += message;
  packed_message += kEndOfTextChar; 
  packed_message += checksum; 
  packed_message += kEndOfTransmissionChar;
  return packed_message;
}

String Communication::getChecksum(String message) {
  byte crc = 0x00;
  int len = message.length();
  int counter = 0;
  while (len--) {
    byte extract = message.charAt(counter);
    counter++;
    for (byte tempI = 8; tempI; tempI--) {
      byte sum = (crc ^ extract) & 0x01;
      crc >>= 1;
      if (sum) {
        crc ^= 0x8C;
      }
      extract >>= 1;
    }
  }
  return String(crc);
}

String Communication::getUnpackedMessage(String message) {
  // Check Start of Header
  if (!checkStartOfHeader(message)) {
    return "";
  }
  
  // Parse Header
  int message_size = parseHeader(message);
  if (message_size < 0) {
    return "";
  }

  // Parse Text
  String unpacked_message = parseText(message); 
  if (unpacked_message == "") {
    return "";
  }

  // Check Message Size
  if (message_size != unpacked_message.length()) {
    return "";
  }
  
  // Compute & Compare Checksums
  String incoming_checksum = parseFooter(message);
  String computed_checksum = getChecksum(unpacked_message);
  if (incoming_checksum != computed_checksum) {
    return "";
  }
  
  // Received Valid Message
  return unpacked_message;
}

bool Communication::checkStartOfHeader(String message) {
  if (message[0] == kStartOfHeaderChar) {
    return 1;
  }
  else {
    return 0;
  }
}

int Communication::parseHeader(String message) {
  int end_char = message.indexOf(kStartOfTextChar);
  if (end_char < 0) {
    return -1;
  }
  return message.substring(1,end_char).toInt();
}

String Communication::parseText(String message) {
  int start_char = message.indexOf(kStartOfTextChar) +1 ;
  int end_char = message.indexOf(kEndOfTextChar);
  if (end_char < 0) {
    return "";
  }
  if (end_char <= start_char) {
    return "";
  }
  return message.substring(start_char,end_char);
}

String Communication::parseFooter(String message) {
  int start_char = message.indexOf(kEndOfTextChar) + 1;
  int end_char = message.length();
  if (end_char < 0) {
    return "";
  }
  if (end_char <= start_char) {
    return "";
  }
  return message.substring(start_char,end_char);
}



char* Communication::floatToString(float value, int places) {
    char outstr[25];
    int minwidth = 0;
    bool rightjustify = false;
    // this is used to write a float value to string, outstr.  oustr is also the return value.
    int digit;
    float tens = 0.1;
    int tenscount = 0;
    int i;
    float tempfloat = value;
    int c = 0;
    int charcount = 1;
    int extra = 0;
    // make sure we round properly. this could use pow from <math.h>, but doesn't seem worth the import
    // if this rounding step isn't here, the value  54.321 prints as 54.3209

    // calculate rounding term d:   0.5/pow(10,places)  
    float d = 0.5;
    if (value < 0)
        d *= -1.0;
    // divide by ten for each decimal place
    for (i = 0; i < places; i++)
        d/= 10.0;    
    // this small addition, combined with truncation will round our values properly 
    tempfloat +=  d;

    // first get value tens to be the large power of ten less than value    
    if (value < 0)
        tempfloat *= -1.0;
    while ((tens * 10.0) <= tempfloat) {
        tens *= 10.0;
        tenscount += 1;
    }

    if (tenscount > 0)
        charcount += tenscount;
    else
        charcount += 1;

    if (value < 0)
        charcount += 1;
    charcount += 1 + places;

    minwidth += 1; // both count the null final character
    if (minwidth > charcount){        
        extra = minwidth - charcount;
        charcount = minwidth;
    }

    if (extra > 0 and rightjustify) {
        for (int i = 0; i< extra; i++) {
            outstr[c++] = ' ';
        }
    }

    // write out the negative if needed
    if (value < 0)
        outstr[c++] = '-';

    if (tenscount == 0) 
        outstr[c++] = '0';

    for (i=0; i< tenscount; i++) {
        digit = (int) (tempfloat/tens);
        itoa(digit, &outstr[c++], 10);
        tempfloat = tempfloat - ((float)digit * tens);
        tens /= 10.0;
    }

    // if no places after decimal, stop now and return

    // otherwise, write the point and continue on
    if (places > 0)
    outstr[c++] = '.';


    // now write out each decimal place by shifting digits one by one into the ones place and writing the truncated value
    for (i = 0; i < places; i++) {
        tempfloat *= 10.0; 
        digit = (int) tempfloat;
        itoa(digit, &outstr[c++], 10);
        // once written, subtract off that digit
        tempfloat = tempfloat - (float) digit; 
    }
    if (extra > 0 and not rightjustify) {
        for (int i = 0; i< extra; i++) {
            outstr[c++] = ' ';
        }
    }

    outstr[c++] = '\0';
    return outstr;
}





