#include <Wire.h>
#include <Adafruit_PWMServoDriver.h>

// Constants
#define HIGHSPEED 4090
#define MEDSPEED 2300
#define LOWSPEED 1000
#define VERYLOWSPEED 500
#define FANOFF 0
#define SPRAYER_PIN 4

// Pattern variables
int cycleDuration = 1000;     // Base time cycle in milliseconds (1 second default)
String sprayPattern = "";     // Will hold the binary pattern
int currentBitIndex = 0;      // Current position in pattern
bool isTransmitting = false;  // Pattern transmission state
unsigned long lastCycleTime = 0;  // For timing control

Adafruit_PWMServoDriver fanController = Adafruit_PWMServoDriver(0x40);

void setup() {
    pinMode(SPRAYER_PIN, OUTPUT);
    Serial.begin(9600);
    fanController.begin();
    fanController.setPWMFreq(30);
}

void loop() {
    if (Serial.available()) {
        String command = Serial.readStringUntil('\n');
        processCommand(command);
    }
    
    // Process pattern if active
    if (isTransmitting && sprayPattern.length() > 0) {
        unsigned long currentTime = millis();
        
        // Check if it's time for the next cycle
        if (currentTime - lastCycleTime >= cycleDuration) {
            processNextCycle();
            lastCycleTime = currentTime;  // Reset timing
        }
    }
}

void processCommand(String command) {
    if (command.startsWith("CONFIG")) {
        // Parse config command: CONFIG,cycleDuration
        int comma = command.indexOf(',');
        cycleDuration = command.substring(comma + 1).toInt();
        Serial.println("Configuration updated");
    }
    else if (command.startsWith("PATTERN")) {
        // Parse pattern command: PATTERN,binarystring
        int comma = command.indexOf(',');
        sprayPattern = command.substring(comma + 1);
        currentBitIndex = 0;
        isTransmitting = true;
        lastCycleTime = millis();  // Initialize timing
        Serial.println("Pattern received");
    }
    else if (command.startsWith("STOP")) {
        stopTransmission();
        Serial.println("Transmission stopped");
    }
    else if (command.indexOf(',') >= 0) {
        // Handle individual fan control: fanNumber,speed
        int comma = command.indexOf(',');
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

void processNextCycle() {
    if (currentBitIndex >= sprayPattern.length()) {
        // Reset to start of pattern instead of stopping
        currentBitIndex = 0;
        Serial.println("Pattern restarting");
    }

    char currentBit = sprayPattern[currentBitIndex];
    if (currentBit == '1') {
        digitalWrite(SPRAYER_PIN, HIGH);
        Serial.print("Spray cycle ");
    } else {
        digitalWrite(SPRAYER_PIN, LOW);
        Serial.print("Wait cycle ");
    }
    
    Serial.print(currentBitIndex + 1);
    Serial.print(" of ");
    Serial.println(sprayPattern.length());
    
    currentBitIndex++;
}

void stopTransmission() {
    isTransmitting = false;
    sprayPattern = "";
    currentBitIndex = 0;
    digitalWrite(SPRAYER_PIN, LOW);
}
