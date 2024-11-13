#include <Wire.h>
#include <Adafruit_PWMServoDriver.h>

// Constants for fan speeds
#define HIGHSPEED 4090
#define MEDSPEED 4000
#define LOWSPEED 1000
#define VERYLOWSPEED 500
#define FANOFF 0

// Pin definitions
#define SPRAYER_PIN 13
const int NUM_SENSORS = 32;  // Total number of sensors through multiplexers

// Multiplexer 1 pins
const int S0_1 = 2;    // Control pins for first multiplexer
const int S1_1 = 3;
const int S2_1 = 4;
const int S3_1 = 5;
const int SIG_1 = A0;   // Analog input for first multiplexer

// Multiplexer 2 pins
const int S0_2 = 6;    // Control pins for second multiplexer
const int S1_2 = 7;
const int S2_2 = 8;
const int S3_2 = 9;
const int SIG_2 = A1;   // Analog input for second multiplexer

// Pattern variables
int cycleDuration = 1000;     // Base cycle time in milliseconds
String sprayPattern = "";     // Binary pattern storage
int currentBitIndex = 0;      // Current position in pattern
bool isTransmitting = false;  // Pattern state
unsigned long lastCycleTime = 0;  // For pattern timing
unsigned long lastSensorTime = 0;  // For sensor timing
const int SENSOR_INTERVAL = 25;   // Sensor reading interval (ms)

// Initialize PWM controller
Adafruit_PWMServoDriver fanController = Adafruit_PWMServoDriver(0x40);

void setup() {
    Serial.begin(115200);
    
    // Initialize PWM controller
    fanController.begin();
    fanController.setPWMFreq(30);
    
    // Initialize sprayer pin
    pinMode(SPRAYER_PIN, OUTPUT);
    digitalWrite(SPRAYER_PIN, LOW);
    
    // Initialize multiplexer control pins
    pinMode(S0_1, OUTPUT); pinMode(S0_2, OUTPUT);
    pinMode(S1_1, OUTPUT); pinMode(S1_2, OUTPUT);
    pinMode(S2_1, OUTPUT); pinMode(S2_2, OUTPUT);
    pinMode(S3_1, OUTPUT); pinMode(S3_2, OUTPUT);
    
    Serial.println("Combined Controller with Multiplexers Initialized");
}

// Function to set multiplexer channel
void setMuxChannel(int channel, int s0, int s1, int s2, int s3) {
    digitalWrite(s0, channel & 0x01);
    digitalWrite(s1, (channel >> 1) & 0x01);
    digitalWrite(s2, (channel >> 2) & 0x01);
    digitalWrite(s3, (channel >> 3) & 0x01);
}

// Function to read a specific sensor through multiplexer
int readMuxSensor(int sensorNumber) {
    if (sensorNumber < 16) {
        // First multiplexer
        setMuxChannel(sensorNumber, S0_1, S1_1, S2_1, S3_1);
        delay(1);
        return analogRead(SIG_1);
    } else {
        // Second multiplexer
        setMuxChannel(sensorNumber - 16, S0_2, S1_2, S2_2, S3_2);
        delay(1);
        return analogRead(SIG_2);
    }
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
    
    // Read and send all sensor values through multiplexers
    for(int i = 0; i < NUM_SENSORS; i++) {
        // Read sensor through appropriate multiplexer
        int value = readMuxSensor(i);
        
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