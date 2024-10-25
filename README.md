# How to run Serial tests
First launch both the gui and whatever test you would like to run
Second set up some form of virtual serial connection(I used [Virtual  Serial port](https://www.virtual-serial-port.org/))
## Fans and sprayer
Connect the tester program to COM2
Connect the fans controller in the gui to COM1
Connect the Sensor controller to Something random
Either Change fan settings or run Sprayer program
The logs will reflect either running
## Sensors
Connect the tester program to COM1
Connect The sensor controller in the gui to COM2
Generate Test data in the tester program
Send Test data in the tester program
The graphs in the GUI will reflect the data sending properly

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
