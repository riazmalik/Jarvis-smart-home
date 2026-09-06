/*
  Relay Test - Test all 4 relays
*/

#define RELAY1 8
#define RELAY2 9
#define RELAY3 10
#define RELAY4 11

void setup() {
  pinMode(RELAY1, OUTPUT);
  pinMode(RELAY2, OUTPUT);
  pinMode(RELAY3, OUTPUT);
  pinMode(RELAY4, OUTPUT);
  
  // Start with all OFF
  digitalWrite(RELAY1, HIGH);
  digitalWrite(RELAY2, HIGH);
  digitalWrite(RELAY3, HIGH);
  digitalWrite(RELAY4, HIGH);
  
  Serial.begin(115200);
  Serial.println("Relay Test Started");
}

void loop() {
  // Turn on each relay one by one
  Serial.println("All ON");
  digitalWrite(RELAY1, LOW);
  digitalWrite(RELAY2, LOW);
  digitalWrite(RELAY3, LOW);
  digitalWrite(RELAY4, LOW);
  delay(2000);
  
  Serial.println("All OFF");
  digitalWrite(RELAY1, HIGH);
  digitalWrite(RELAY2, HIGH);
  digitalWrite(RELAY3, HIGH);
  digitalWrite(RELAY4, HIGH);
  delay(2000);
}