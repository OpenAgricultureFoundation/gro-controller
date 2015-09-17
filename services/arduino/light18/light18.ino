int light_pin = 8;

void setup() {
  pinMode(light_pin,OUTPUT);
}

void loop() {
  digitalWrite(light_pin, LOW); // turn on
  delay(4000);
  digitalWrite(light_pin, HIGH); // turn off
  delay(1000);
}
