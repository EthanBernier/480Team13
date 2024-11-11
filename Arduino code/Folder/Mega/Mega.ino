#include <Wire.h>
#include <Adafruit_PWMServoDriver.h>

// Constants for fan speeds
#define HIGHSPEED 4090
#define MEDSPEED 4000
#define LOWSPEED 1000
#define VERYLOWSPEED 500
#define FANOFF 0

// Pin definitions
#define SPRAYER_PIN 4
const int NUM_SENSORS = 10;  // A0-A9
const int START_PIN = A0;

// Pattern variables
int cycleDuration = 1000;     // Base cycle time in milliseconds
String sprayPattern = "";     // Binary pattern storage
int currentBitIndex = 0;      // Current position in pattern
bool isTransmitting = false;  // Pattern state
unsigned long lastCycleTime = 0;  // For pattern timing
unsigned long lastSensorTime = 0;  // For sensor timing
const int SENSOR_INTERVAL = 50;   // Sensor reading interval (ms)

// Initialize PWM controller
Adafruit_PWMServoDriver fanController = Adafruit_PWMServoDriver(0x40);

void setup() {
    Serial.begin(115200);
    
    // Initialize PWM controller
    fanController.begin();
    fanController.setPWMFreq(30);
    
    // Initialize pins
    pinMode(SPRAYER_PIN, OUTPUT);
    digitalWrite(SPRAYER_PIN, LOW);
    
    // Initialize sensor pins
    for(int i = 0; i < NUM_SENSORS; i++) {
        pinMode(START_PIN + i, INPUT);
    }
    
    Serial.println("Combined Controller Initialized");
}

void loop() {
    // Check for commands
    if (Serial.available()) {
        String command = Serial.readStringUntil('\n');
        processCommand(command);
    }
    
    // Handle spray pattern if active
    if (isTransmitting && sprayPattern.length() > 0) {
        unsigned long currentTime = millis();
        if (currentTime - lastCycleTime >= cycleDuration) {
            processNextCycle();
            lastCycleTime = currentTime;
        }
    }
    
    // Handle sensor readings
    unsigned long currentTime = millis();
    if (currentTime - lastSensorTime >= SENSOR_INTERVAL) {
        sendSensorData();
        lastSensorTime = currentTime;
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
        lastCycleTime = millis();
        Serial.println("Pattern received");
    }
    else if (command.startsWith("STOP")) {
        stopSprayPattern();
        Serial.println("Pattern stopped");
    }
    else if (command.indexOf(',') >= 0) {
        // Handle fan control: fanNumber,speed
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
            Serial.print("Fan ");
            Serial.print(fan);
            Serial.print(" set to speed ");
            Serial.println(speed);
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

void stopSprayPattern() {
    isTransmitting = false;
    sprayPattern = "";
    currentBitIndex = 0;
    digitalWrite(SPRAYER_PIN, LOW);
}

void sendSensorData() {
    // Start of data packet
    Serial.print("START,");
    Serial.print(millis());
    Serial.print(",");
    
    // Read and send all sensor values
    for(int i = 0; i < NUM_SENSORS; i++) {
        // Read sensor
        int value = analogRead(START_PIN + i);
        
        // Send in format GUI expects
        Serial.print("S");
        Serial.print(i + 1);  // GUI expects 1-based sensor numbers
        Serial.print(":");
        Serial.print(value);
        
        // Add comma if not last sensor
        if(i < NUM_SENSORS - 1) {
            Serial.print(",");
        }
    }
    
    // End of data packet
    Serial.println(",END");
}