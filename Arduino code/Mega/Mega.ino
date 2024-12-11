#include <Wire.h>
#include <Adafruit_PWMServoDriver.h>
#include <light_CD74HC4067.h>

// Constants for fan speeds
#define HIGHSPEED 4090
#define MEDSPEED 4000
#define LOWSPEED 1000
#define VERYLOWSPEED 500
#define FANOFF 0

#define SPRAYER_PIN 13
const int NUM_SENSORS = 32;

// Multiplexer signal pins
const int SIG_1 = A0;
const int SIG_2 = A1;

CD74HC4067 mux1(2, 3, 4, 5);    // First multiplexer
CD74HC4067 mux2(6, 7, 8, 9);    // Second multiplexer

// Pattern variables
int cycleDuration = 1000;
String sprayPattern = "";
volatile int currentBitIndex = 0;
volatile bool isTransmitting = false;
unsigned long lastCycleTime = 0;
unsigned long lastSensorTime = 0;
const int SENSOR_INTERVAL = 10;

String inputBuffer = "";
Adafruit_PWMServoDriver fanController = Adafruit_PWMServoDriver(0x40);

void setup() {
    Serial.begin(115200);
    fanController.begin();
    fanController.setPWMFreq(30);
    pinMode(SPRAYER_PIN, OUTPUT);
    digitalWrite(SPRAYER_PIN, LOW);
    pinMode(SIG_1, INPUT);
    pinMode(SIG_2, INPUT);
}

void loop() {
    while (Serial.available()) {
        char c = Serial.read();
        if (c == '\n') {
            processCommand(inputBuffer);
            inputBuffer = "";
        } else {
            inputBuffer += c;
        }
    }

    unsigned long currentTime = millis();

    if (isTransmitting && sprayPattern.length() > 0) {
        if (currentTime - lastCycleTime >= cycleDuration) {
            processNextCycle();
            lastCycleTime = currentTime;
        }
    }

    if (currentTime - lastSensorTime >= SENSOR_INTERVAL) {
        sendSensorData();
        lastSensorTime = currentTime;
    }
}

void processCommand(String command) {
    if (command.startsWith("CONFIG")) {
        int comma = command.indexOf(',');
        if (comma != -1) {
            cycleDuration = command.substring(comma + 1).toInt();
        }
    }
    else if (command.startsWith("PATTERN")) {
        int comma = command.indexOf(',');
        if (comma != -1) {
            sprayPattern = command.substring(comma + 1);
            currentBitIndex = 0;
            isTransmitting = true;
            lastCycleTime = millis();
            processNextCycle();
        }
    }
    else if (command == "STOP") {
        stopSprayPattern();
    }
    else if (command.indexOf(',') >= 0) {
        int comma = command.indexOf(',');
        if (comma != -1) {
            int fan = command.substring(0, comma).toInt();
            int speed = command.substring(comma + 1).toInt();
            
            if (fan >= 0 && fan < 16) {
                int pwmValue;
                switch(speed) {
                    case 0: pwmValue = FANOFF; break;
                    case 1: pwmValue = VERYLOWSPEED; break;
                    case 2: pwmValue = LOWSPEED; break;
                    case 3: pwmValue = MEDSPEED; break;
                    case 4: pwmValue = HIGHSPEED; break;
                    default: pwmValue = FANOFF;
                }
                fanController.setPWM(fan, 0, pwmValue);
            }
        }
    }
}

void processNextCycle() {
    if (currentBitIndex >= sprayPattern.length()) {
        currentBitIndex = 0;
    }

    digitalWrite(SPRAYER_PIN, sprayPattern[currentBitIndex] == '1' ? HIGH : LOW);
    currentBitIndex++;
}

void stopSprayPattern() {
    isTransmitting = false;
    sprayPattern = "";
    currentBitIndex = 0;
    digitalWrite(SPRAYER_PIN, LOW);
}

void sendSensorData() {
    Serial.print("$");  // Start marker
    Serial.print(millis());
    Serial.print(",");
    
    // First read all MUX1 sensors
    for(int i = 0; i < 16; i++) {
        mux1.channel(i);
        delay(1);
        int value = analogRead(SIG_1);
        Serial.print(value);
        Serial.print(",");
    }
    
    // Then read all MUX2 sensors
    for(int i = 0; i < 16; i++) {
        mux2.channel(i);
        delay(1);
        int value = analogRead(SIG_2);
        Serial.print(value);
        if(i < 15) Serial.print(",");  // Don't add comma after last value
    }
    
    Serial.println();  // End of data marker
}