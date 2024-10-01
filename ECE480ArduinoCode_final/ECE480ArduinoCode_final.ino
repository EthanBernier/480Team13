#include <Wire.h>  ///include this libarary it is available on GITHUB
#include <Adafruit_PWMServoDriver.h> ////Available on GITHUB 

Adafruit_PWMServoDriver myServo = Adafruit_PWMServoDriver(0x40); // Every PWM expander is set to this.



uint8_t servonum = 0;

void setup() {
  Serial.begin(9600); // set baud rate
  myServo.begin(); 
  myServo.setPWMFreq(30); //30 Hz
  delay(10);
  //// intitalize pins on the expander to low
   myServo.setPWM(0,0,1000); // set pin 0 on expander to 0/low
  delay(1);
  myServo.setPWM(1,0,0);  //set pin 1 on expander to 0/low
  delay(1);
  myServo.setPWM(2, 0, 0);
  delay(1);
  myServo.setPWM(3, 0, 0);
  delay(1);
    myServo.setPWM(4,0,0);
  delay(1);
  myServo.setPWM(5, 0, 0);
  delay(1);
  myServo.setPWM(6, 0, 0);
  delay(1);
   myServo.setPWM(7,0,0);
  delay(1);
  myServo.setPWM(8, 0, 0);
  delay(1);
  myServo.setPWM(9, 0, 0);
  delay(1);
    myServo.setPWM(10,0,0);
  delay(1);
  myServo.setPWM(11, 0, 0);
  delay(1);
  myServo.setPWM(12, 0, 0);
  delay(1);
   myServo.setPWM(13,0,0);
  delay(1);
  myServo.setPWM(14, 0, 0);
  delay(1);
  myServo.setPWM(15, 0, 0);
  delay(1);
    
 
 
}
void loop() {
  if(Serial.available()) {
    char val = Serial.read(); // looking for byte sent from Processing IDE

    if(val == '0') {
        myServo.setPWM(0,0,2000); // 2000 is the slow speed setting on pin 0
    }
    if(val == '1'){
        myServo.setPWM(0,0,3000); /// 3000 is the Med speed setting on pin 0
    }
    if(val == '2') {
       myServo.setPWM(0,0,4000);  /// 4000 is the Fast speed. Any values between 0-4000 will change the fan speed
    }
    if(val == '3')
    {
        myServo.setPWM(0,0,0);
    }
    if(val=='4'){
        myServo.setPWM(1,0,2000);
    }
    if(val=='5'){
        myServo.setPWM(1,0,3000);   
    }
    if(val=='6'){
       myServo.setPWM(1,0,4000);
    }
    if(val=='7'){
        myServo.setPWM(1,0,0);
        }
    if(val=='8')
    {
        myServo.setPWM(2,0,2000);
    }
    if(val=='9')
    {
       myServo.setPWM(2,0,3000);
    }
    if(val == 'a'){
        myServo.setPWM(2,0,4000);
    }
    if(val=='b'){
        myServo.setPWM(2,0,0);
    }
     if(val=='c')
    {
        myServo.setPWM(3,0,2000);
    }
    if(val=='d')
    {
       myServo.setPWM(3,0,3000);
    }
    if(val == 'e'){
        myServo.setPWM(3,0,4000);
    }
    if(val=='f'){
        myServo.setPWM(3,0,0);
    }
    if(val=='g')
    {
        myServo.setPWM(4,0,2000);
    }
    if(val=='h')
    {
       myServo.setPWM(4,0,3000);
    }
    if(val == 'i'){
        myServo.setPWM(4,0,4000);
    }
    if(val=='j'){
        myServo.setPWM(4,0,0);
    }
    if(val=='k')
    {
        myServo.setPWM(5,0,2000);
    }
    if(val=='l')
    {
       myServo.setPWM(5,0,3000);
    }
    if(val == 'm'){
        myServo.setPWM(5,0,4000);
    }
    if(val=='n'){
        myServo.setPWM(5,0,0);
    }
    if(val=='O')
    {
        myServo.setPWM(6,0,2000);
    }
    if(val=='p')
    {
       myServo.setPWM(6,0,3000);
    }
    if(val == 'q'){
        myServo.setPWM(6,0,4000);
    }
    if(val=='r'){
        myServo.setPWM(6,0,0);
    }
    if(val=='s')
    {
        myServo.setPWM(7,0,2000);
    }
    if(val=='t')
    {
       myServo.setPWM(7,0,3000);
    }
    if(val == 'u'){
        myServo.setPWM(7,0,4000);
    }
    if(val=='v'){
        myServo.setPWM(7,0,0);
    }
    if(val=='w')
    {
        myServo.setPWM(8,0,2000);
    }
    if(val=='x')
    {
       myServo.setPWM(8,0,3000);
    }
    if(val == 'y'){
        myServo.setPWM(8,0,4000);
    }
    if(val=='z'){
        myServo.setPWM(8,0,0);
    }
    
  if(val=='A')
    {
        myServo.setPWM(9,0,2000);
    }
    if(val=='B')
    {
       myServo.setPWM(9,0,3000);
    }
    if(val == 'C'){
        myServo.setPWM(9,0,4000);
    }
    if(val == 'D'){
        myServo.setPWM(9,0,0);  
    }
    if(val=='E')
    {
        myServo.setPWM(10,0,2000);
    }
    if(val=='F')
    {
       myServo.setPWM(10,0,3000);
    }
    if(val == 'G'){
        myServo.setPWM(10,0,4000);
    }
    if(val == 'H'){
        myServo.setPWM(10,0,0);  
    }
    if(val=='I')
    {
        myServo.setPWM(11,0,2000);
    }
    if(val=='J')
    {
       myServo.setPWM(11,0,3000);
    }
    if(val == 'K'){
        myServo.setPWM(11,0,4000);
    }
    if(val == 'L'){
        myServo.setPWM(11,0,0);  
    }
    if(val=='M')
    {
        myServo.setPWM(12,0,2000);
    }
    if(val=='N')
    {
       myServo.setPWM(12,0,3000);
    }
    if(val == '~'){
        myServo.setPWM(12,0,4000);
    }
    if(val == 'P'){
        myServo.setPWM(12,0,0);  
    }
    if(val=='Q')
    {
        myServo.setPWM(13,0,2000);
    }
    if(val=='R')
    {
       myServo.setPWM(13,0,3000);
    }
    if(val == 'S'){
        myServo.setPWM(13,0,4000);
    }
    if(val == 'T'){
        myServo.setPWM(13,0,0);  
    }
    if(val=='U')
    {
        myServo.setPWM(14,0,2000);
    }
    if(val=='V')
    {
       myServo.setPWM(14,0,3000);
    }
    if(val == 'W'){
        myServo.setPWM(14,0,4000);
    }
    if(val == 'X'){
        myServo.setPWM(14,0,0);  
    }
    if(val=='Y')
    {
        myServo.setPWM(15,0,2000);
    }
    if(val=='Z')
    {
       myServo.setPWM(15,0,3000);
    }
    if(val == ';'){
        myServo.setPWM(15,0,4000);
    }
    if(val == ']'){
        myServo.setPWM(15,0,0);  
    }
    if(val == '+')   /// all off master command
    {
    myServo.setPWM(0,0,0);
  delay(1);
  myServo.setPWM(1,0,0);
  delay(1);
  myServo.setPWM(2, 0, 0);
  delay(1);
  myServo.setPWM(3, 0, 0);
  delay(1);
    myServo.setPWM(4,0,0);
  delay(1);
  myServo.setPWM(5, 0, 0);
  delay(1);
  myServo.setPWM(6, 0, 0);
  delay(1);
   myServo.setPWM(7,0,0);
  delay(1);
  myServo.setPWM(8, 0, 0);
  delay(1);
  myServo.setPWM(9, 0, 0);
  delay(1);
    myServo.setPWM(10,0,0);
  delay(1);
  myServo.setPWM(11, 0, 0);
  delay(1);
  myServo.setPWM(12, 0, 0);
  delay(1);
   myServo.setPWM(13,0,0);
  delay(1);
  myServo.setPWM(14, 0, 0);
  delay(1);
  myServo.setPWM(15, 0, 0);
  delay(1);
    
    }
   if(val == '&') // col 1 command
    {
    myServo.setPWM(0,0,4000);
  delay(1);
  myServo.setPWM(1,0,0);
  delay(1);
  myServo.setPWM(2, 0, 0);
  delay(1);
  myServo.setPWM(3, 0, 0);
  delay(1);
    myServo.setPWM(4,0,4000);
  delay(1);
  myServo.setPWM(5, 0, 0);
  delay(1);
  myServo.setPWM(6, 0, 0);
  delay(1);
   myServo.setPWM(7,0,0);
  delay(1);
  myServo.setPWM(8, 0, 4000);
  delay(1);
  myServo.setPWM(9, 0, 0);
  delay(1);
    myServo.setPWM(10,0,0);
  delay(1);
  myServo.setPWM(11, 0, 0);
  delay(1);
  myServo.setPWM(12, 0, 4000);
  delay(1);
   myServo.setPWM(13,0,0);
  delay(1);
  myServo.setPWM(14, 0, 0);
  delay(1);
  myServo.setPWM(15, 0, 0);
  delay(1);
    
    }
   if(val == '%')   // col2 command
    {
    myServo.setPWM(0,0,0);
  delay(1);
  myServo.setPWM(1,0,4000);
  delay(1);
  myServo.setPWM(2, 0, 0);
  delay(1);
  myServo.setPWM(3, 0, 0);
  delay(1);
    myServo.setPWM(4,0,0);
  delay(1);
  myServo.setPWM(5, 0, 4000);
  delay(1);
  myServo.setPWM(6, 0, 0);
  delay(1);
   myServo.setPWM(7,0,0);
  delay(1);
  myServo.setPWM(8, 0, 0);
  delay(1);
  myServo.setPWM(9, 0, 4000);
  delay(1);
    myServo.setPWM(10,0,0);
  delay(1);
  myServo.setPWM(11, 0, 0);
  delay(1);
  myServo.setPWM(12, 0, 0);
  delay(1);
   myServo.setPWM(13,0,4000);
  delay(1);
  myServo.setPWM(14, 0, 0);
  delay(1);
  myServo.setPWM(15, 0, 0);
  delay(1);
    
    }  
    if(val == '$')   /// col 3 command
    {
    myServo.setPWM(0,0,0);
  delay(1);
  myServo.setPWM(1,0,0);
  delay(1);
  myServo.setPWM(2, 0, 4000);
  delay(1);
  myServo.setPWM(3, 0, 0);
  delay(1);
    myServo.setPWM(4,0,0);
  delay(1);
  myServo.setPWM(5, 0, 0);
  delay(1);
  myServo.setPWM(6, 0, 4000);
  delay(1);
   myServo.setPWM(7,0,0);
  delay(1);
  myServo.setPWM(8, 0, 0);
  delay(1);
  myServo.setPWM(9, 0, 0);
  delay(1);
    myServo.setPWM(10,0,4000);
  delay(1);
  myServo.setPWM(11, 0, 0);
  delay(1);
  myServo.setPWM(12, 0, 0);
  delay(1);
   myServo.setPWM(13,0,0);
  delay(1);
  myServo.setPWM(14, 0, 4000);
  delay(1);
  myServo.setPWM(15, 0, 0);
  delay(1);
    
    }
     if(val == '#')   /// col 4 command
    {
    myServo.setPWM(0,0,0);
  delay(1);
  myServo.setPWM(1,0,0);
  delay(1);
  myServo.setPWM(2, 0, 0);
  delay(1);
  myServo.setPWM(3, 0, 4000);
  delay(1);
    myServo.setPWM(4,0,0);
  delay(1);
  myServo.setPWM(5, 0, 0);
  delay(1);
  myServo.setPWM(6, 0, 0);
  delay(1);
   myServo.setPWM(7,0,4000);
  delay(1);
  myServo.setPWM(8, 0, 0);
  delay(1);
  myServo.setPWM(9, 0, 0);
  delay(1);
    myServo.setPWM(10,0,0);
  delay(1);
  myServo.setPWM(11, 0, 4000);
  delay(1);
  myServo.setPWM(12, 0, 0);
  delay(1);
   myServo.setPWM(13,0,0);
  delay(1);
  myServo.setPWM(14, 0, 0);
  delay(1);
  myServo.setPWM(15, 0, 4000);
  delay(1);
    
    }
    if(val == '*')   /// top left command
    {
    myServo.setPWM(0,0,4000);
  delay(1);
  myServo.setPWM(1,0,4000);
  delay(1);
  myServo.setPWM(2, 0, 0);
  delay(1);
  myServo.setPWM(3, 0, 0);
  delay(1);
    myServo.setPWM(4,0,4000);
  delay(1);
  myServo.setPWM(5, 0, 4000);
  delay(1);
  myServo.setPWM(6, 0, 0);
  delay(1);
   myServo.setPWM(7,0,0);
  delay(1);
  myServo.setPWM(8, 0, 0);
  delay(1);
  myServo.setPWM(9, 0, 0);
  delay(1);
    myServo.setPWM(10,0,0);
  delay(1);
  myServo.setPWM(11, 0, 0);
  delay(1);
  myServo.setPWM(12, 0, 0);
  delay(1);
   myServo.setPWM(13,0,0);
  delay(1);
  myServo.setPWM(14, 0, 0);
  delay(1);
  myServo.setPWM(15, 0, 0);
  delay(1);
    
    }
     if(val == ')')  ///top right command
    {
    myServo.setPWM(0,0,0);
  delay(1);
  myServo.setPWM(1,0,0);
  delay(1);
  myServo.setPWM(2, 0, 4000);
  delay(1);
  myServo.setPWM(3, 0, 4000);
  delay(1);
    myServo.setPWM(4,0,0);
  delay(1);
  myServo.setPWM(5, 0, 0);
  delay(1);
  myServo.setPWM(6, 0, 4000);
  delay(1);
   myServo.setPWM(7,0,4000);
  delay(1);
  myServo.setPWM(8, 0, 0);
  delay(1);
  myServo.setPWM(9, 0, 0);
  delay(1);
    myServo.setPWM(10,0,0);
  delay(1);
  myServo.setPWM(11, 0, 0);
  delay(1);
  myServo.setPWM(12, 0, 0);
  delay(1);
   myServo.setPWM(13,0,0);
  delay(1);
  myServo.setPWM(14, 0, 0);
  delay(1);
  myServo.setPWM(15, 0, 0);
  delay(1);
    
    }
    if(val == '(')  ///Bottom left command
    {
    myServo.setPWM(0,0,0);
  delay(1);
  myServo.setPWM(1,0,0);
  delay(1);
  myServo.setPWM(2, 0, 0);
  delay(1);
  myServo.setPWM(3, 0, 0);
  delay(1);
    myServo.setPWM(4,0,0);
  delay(1);
  myServo.setPWM(5, 0, 0);
  delay(1);
  myServo.setPWM(6, 0, 0);
  delay(1);
   myServo.setPWM(7,0,0);
  delay(1);
  myServo.setPWM(8, 0, 4000);
  delay(1);
  myServo.setPWM(9, 0, 4000);
  delay(1);
    myServo.setPWM(10,0,0);
  delay(1);
  myServo.setPWM(11, 0, 0);
  delay(1);
  myServo.setPWM(12, 0, 4000);
  delay(1);
   myServo.setPWM(13,0,4000);
  delay(1);
  myServo.setPWM(14, 0, 0);
  delay(1);
  myServo.setPWM(15, 0, 0);
  delay(1);
    
    }
     if(val == '^')  ///bottom right command
    {
    myServo.setPWM(0,0,0);
  delay(1);
  myServo.setPWM(1,0,0);
  delay(1);
  myServo.setPWM(2, 0, 0);
  delay(1);
  myServo.setPWM(3, 0, 0);
  delay(1);
    myServo.setPWM(4,0,0);
  delay(1);
  myServo.setPWM(5, 0, 0);
  delay(1);
  myServo.setPWM(6, 0, 0);
  delay(1);
   myServo.setPWM(7,0,0);
  delay(1);
  myServo.setPWM(8, 0, 0);
  delay(1);
  myServo.setPWM(9, 0, 0);
  delay(1);
    myServo.setPWM(10,0,4000);
  delay(1);
  myServo.setPWM(11, 0, 4000);
  delay(1);
  myServo.setPWM(12, 0, 0);
  delay(1);
   myServo.setPWM(13,0,0);
  delay(1);
  myServo.setPWM(14, 0, 4000);
  delay(1);
  myServo.setPWM(15, 0, 4000);
  delay(1);
    
    }
     if(val == '@')  ///Center focus command lol
    {
    myServo.setPWM(0,0,2000);
  delay(1);
  myServo.setPWM(1,0,2000);
  delay(1);
  myServo.setPWM(2, 0, 2000);
  delay(1);
  myServo.setPWM(3, 0, 2000);
  delay(1);
    myServo.setPWM(4,0,2000);
  delay(1);
  myServo.setPWM(5, 0, 4000);
  delay(1);
  myServo.setPWM(6, 0, 4000);
  delay(1);
   myServo.setPWM(7,0,2000);
  delay(1);
  myServo.setPWM(8, 0, 2000);
  delay(1);
  myServo.setPWM(9, 0, 4000);
  delay(1);
    myServo.setPWM(10,0,4000);
  delay(1);
  myServo.setPWM(11, 0, 2000);
  delay(1);
  myServo.setPWM(12, 0, 2000);
  delay(1);
   myServo.setPWM(13,0,2000);
  delay(1);
  myServo.setPWM(14, 0, 2000);
  delay(1);
  myServo.setPWM(15, 0, 2000);
  delay(1);
    
    }
    
}}
