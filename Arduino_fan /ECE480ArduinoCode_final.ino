#include <Wire.h>
#include <Adafruit_PWMServoDriver.h>

Adafruit_PWMServoDriver fanController = Adafruit_PWMServoDriver(0x40);

// Fan speed constants
const int SPEED_OFF = 0;
const int SPEED_LOW = 2000;
const int SPEED_MED = 3000;
const int SPEED_HIGH = 4000;

void setup() {
  Serial.begin(9600);
  fanController.begin();
  fanController.setPWMFreq(30); // 30 Hz

  // Initialize all fans to off
  for(int i = 0; i < 16; i++) {
    fanController.setPWM(i, 0, SPEED_OFF);
    delay(1);
  }
}

void loop() {
  if(Serial.available()) {
    // Expect format: <fan_number>,<speed>
    // fan_number: 0-15
    // speed: 0 (off), 1 (low), 2 (med), 3 (high)

    String command = Serial.readStringUntil('\n');
    int fan = command.substring(0, command.indexOf(',')).toInt();
    int speed = command.substring(command.indexOf(',') + 1).toInt();

    if(fan >= 0 && fan < 16) {
      int pwmValue;
      switch(speed) {
        case 0: pwmValue = SPEED_OFF; break;
        case 1: pwmValue = SPEED_LOW; break;
        case 2: pwmValue = SPEED_MED; break;
        case 3: pwmValue = SPEED_HIGH; break;
        default: pwmValue = SPEED_OFF;
      }
      fanController.setPWM(fan, 0, pwmValue);
    }
  }
}