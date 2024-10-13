% Define Arduino object
arduinoObj = arduino('usbmodem1101', 'Uno');

% Define the number of samples and time delay
numSamples = 100;
timeDelay = 0.1;

% Initialize data arrays
sensorData = zeros(1, numSamples);
timeStamps = zeros(1, numSamples);

% Create figure for real-time plot
figure;
plotHandle = plot(timeStamps, sensorData);
title('Real-time Sensor Data');
xlabel('Time (s)');
ylabel('Sensor Value');

% Open file for data saving
fileID = fopen('sensor_data.txt', 'w');

% Loop for real-time data acquisition
for i = 1:numSamples
    % Read sensor value from A0
    sensorValue = readVoltage(arduinoObj, 'A0');
    
    % Record timestamp
    timeStamp = i * timeDelay;
    
    % Update data arrays
    sensorData(i) = sensorValue;
    timeStamps(i) = timeStamp;
    
    % Update real-time plot
    set(plotHandle, 'XData', timeStamps, 'YData', sensorData);
    drawnow;
    
    % Save data to file
    fprintf(fileID, '%f, %f\n', timeStamp, sensorValue);
    
    % Pause for time delay
    pause(timeDelay);
end

% Close file
fclose(fileID);

% Disconnect Arduino
clear arduinoObj;
disp('Data acquisition completed and saved.');
