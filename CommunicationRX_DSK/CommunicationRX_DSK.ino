const int sensor1A0 = A0;
const int sensor1A1 = A1;
const int sensor2A0 = A2;
const int sensor2A1 = A3;


void setup() {
   Serial.begin(9600);
}

  void loop() {
    // put your main code here, to run repeatedly:
    // bool change = false;
    // static uint32_t t = millis();
    int sensor1ValueA0 = analogRead(sensor1A0);
    int sensor1ValueA1 = analogRead(sensor1A1);
    int sensor2ValueA0 = analogRead(sensor2A0);
    int sensor2ValueA1 = analogRead(sensor2A1);
    // Send data to the serial port
    Serial.print("S1A0:");
    Serial.print(sensor1ValueA0);
    Serial.print(",S1A1:");
    Serial.print(sensor1ValueA1);
    Serial.print(",S2A0:");
    Serial.print(sensor2ValueA0);
    Serial.print(",S2A1:");
    Serial.println(sensor2ValueA1);   

    delay(200);
    
  }
