const int sensorPinA0 = A0;
const int sensorPinA1 = A1;
void setup() {
Serial.begin(9600);
}
void loop() {
 // put your main code here, to run repeatedly:
 // bool change = false;
 // static uint32_t t = millis();
int sensorValueA0 = analogRead(sensorPinA0);
int sensorValueA1 = analogRead(sensorPinA1);
 // Send data to the serial port
Serial.print("A0:");
Serial.print(sensorValueA0);
Serial.print(",A1:");
Serial.println(sensorValueA1);
delay(200);
}