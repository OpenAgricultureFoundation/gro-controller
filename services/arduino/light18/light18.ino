int light_pin = 8;
const int hour_in_ms = 3600000;

void setup() {
  pinMode(light_pin,OUTPUT);
}

void loop() {
  digitalWrite(light_pin, LOW); // turn on
  delay(hour_in_ms*18);
  digitalWrite(light_pin, HIGH); // turn off
  delay(hour_in_ms*6);
}
