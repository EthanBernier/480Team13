# How to run the sensor data script
 - First make sure the new sensor code(CommunicationRX_DSK) is flashed to the arduino
 - Next load the python script(in Sensor data processing) as well as its packages
 - In the script change the serial port to be that of the arduino on line 9
 - When ran the script gathers 60 seconds of data change that on line 11 if you want it to run for more or less
 - Open the markdown file in Obsidian after the script is done running
 
```mermaid
graph TD
    A[Python Code] -->|Serial Communication| B[Arduino Mega]
    B -->|Control Signals| C[Fan Array]
    B -->|Control Signals| D[Sprayer]
    B -->|Receive Data| E[Sensor Array]
    
    F[MQ3 Sensor] -->|Analog Data| E
    G[MICS5524 Sensor] -->|Analog Data| E
    
    E -->|Sensor Readings| B
    B -->|Serial Data| A
    
    A -->|Process Data| H[Data Logging]
    A -->|Generate| I[Visualizations]
    A -->|User Input| J[Control Commands]
    

    
    K[User Interface] -->|Input| A
    A -->|Display| K
```
