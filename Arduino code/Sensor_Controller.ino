const int NUM_SENSORS = 16;
const int SENSORS_PER_BOARD = 2;
const int NUM_BOARDS = NUM_SENSORS / SENSORS_PER_BOARD;

// Define an array to store all sensor pins
const int sensorPins[NUM_SENSORS][SENSORS_PER_BOARD] = {
  {A0, A1}, {A2, A3}, {A4, A5}, {A6, A7},
  {A8, A9}, {A10, A11}, {A12, A13}, {A14, A15},
  {A0, A1}, {A2, A3}, {A4, A5}, {A6, A7},
  {A8, A9}, {A10, A11}, {A12, A13}, {A14, A15}
};

void setup() {
  Serial.begin(115200);  // Increased baud rate for faster data transmission(change it both in here and the python script if you do change it)
}

void loop() {
  unsigned long timestamp = millis();
  
  // Start of data packet
  Serial.print("START,");
  Serial.print(timestamp);
  Serial.print(",");

  for (int i = 0; i < NUM_SENSORS; i++) {
    for (int j = 0; j < SENSORS_PER_BOARD; j++) {
      int sensorValue = analogRead(sensorPins[i][j]);
      
      Serial.print("S");
      Serial.print(i + 1);
      Serial.print("A");
      Serial.print(j);
      Serial.print(":");
      Serial.print(sensorValue);
      if (i < NUM_SENSORS - 1 || j < SENSORS_PER_BOARD - 1) {
        Serial.print(",");
      }
    }
  }
  
  // End of data packet
  Serial.println(",END");
  
  delay(200);
}