
/*  Ball Levitation in tube trainer for PID
    Written by Corey Blankenship and Dylan Cook
    Nathir Rawashdeh Advisor
    Michigan Technological University
    Spring 2021 - Fall 2024

   PINOUT
   A0, A1, A2 - Potentiometers for PID Gain
   2 (BLUE) & 3 (PURPLE) SCL/SDA for TOF sensor
   6,7- Switches
   9 - PWM output

    SetSampleTime: The sensor values jitter a bit with a still target.  If the sample time is too small, the Output jitters
    from this noise from the sensor.  Using larger sample time will average the values and smooth the output.  But making
    the sample times too large will make the corrections jerky.  Experiment with SetSampleTime values to get the desired
    output.
*/

#include "Adafruit_VL53L0X.h"  // Distance Measurement Library 
#include <PID_v1.h>            // PID Library

Adafruit_VL53L0X lox = Adafruit_VL53L0X();

//Servo myservo;                      // create servo object to control a servo
double Setpoint, Input, Output;     // PID Variables
double Kp = .6, Ki = .3, Kd = 1.6;  //.3,.15,.4
unsigned long sTime = 100;
int pPin = A0;           // Analog pot pin for P
int iPin = A1;           // Analog pot pin for I
int dPin = A2;           // Analog pot pin for D
int servoPin = A3;
int iSwitch = 6;        //Digital input for i DPDT switch
int dSwitch = 7;        //Digital input for d DPDT switch
const byte OC1A_PIN = 9;
const byte OC1B_PIN = 10;
const word PWM_FREQ_HZ = 15000; //Adjust this value to adjust the frequency
const word TCNT1_TOP = 16000000 / (2 * PWM_FREQ_HZ);
const unsigned long TIMEOUT = 1;
int previousValidData = 0;

PID myPID(&Input, &Output, &Setpoint, Kp, Ki, Kd, TWAR);
unsigned long timer = 0;      // Not Used
unsigned long prevTime = 0;   // Set Point Timer
const long interval = 15000;  // Set Point Timer Interval
int setPos = LOW;             // Set Point Position

void setPwmDuty(byte duty) {
  //int duty = analogRead(dPin)/10;
  OCR1A = (word) (duty * TCNT1_TOP) / 100;
  //Serial.println("OCR1A: " + String(OCR1A));
}

void setup() {
  pinMode(OC1A_PIN, OUTPUT);
  // Clear Timer1 control and count registers
  TCCR1A = 0;
  TCCR1B = 0;
  TCNT1  = 0;
  //int long timeou = 500000;
  //lox.setMeasurementTimingBudgetMicroSeconds(timeou);

  previousValidData = 0;

  //   Set Timer1 configuration
  // COM1A(1:0) = 0b10;   //(Output A clear rising/set falling)
  // COM1B(1:0) = 0b00;   //(Output B normal operation)
  // WGM(13:10) = 0b1010; //(Phase correct PWM)
  // ICNC1      = 0b0;    //(Input capture noise canceler disabled)
  // ICES1      = 0b0;    //(Input capture edge select disabled)
  //CS(12:10)  = 0b001;   //(Input clock select = clock/1)


  TCCR1A |= (1 << COM1A1) | (1 << WGM11);
  TCCR1B |= (1 << WGM13)  | (1 << CS10);
  ICR1 = TCNT1_TOP;

  Serial.begin(9600);
  while (! Serial) {        // wait until serial port opens for native USB devices
    delay(1);
  }

  if (!lox.begin()) {         // Setup for L0X distance measurement
    Serial.println(F("Failed to boot VL53L0X"));
    while (1);
  }

  //myservo.attach(9);                // attaches the servo on pin 9 to the servo object
  myPID.SetMode(AUTOMATIC);
  myPID.SetOutputLimits(0,75);    // Fan PWM Min, Max
  myPID.SetSampleTime(sTime);       // 200 ** Smaller Values produce more jitter from the sensor, larger values smooth jitter
  //Setpoint = sp1;                   // initialize setpoint
  pinMode(iSwitch, INPUT_PULLUP);         //Stage switch (I)
  pinMode(dSwitch, INPUT_PULLUP);         //Stage switch (D)
}


void loop() {
  //float heightNum = analogRead(iPin) / 1023.0;    // once you hook up a height potentiometer, change iPin to that.
  //int newSetpoint = 400 * heightNum;        
  Setpoint = 250;                           // New setpoint value 1
  readPots();                                   // Read data from potentiometers
  getDataWithTimeout(TIMEOUT);                   // Read distance (location of ball)
  int range = ReadDist();
  myPID.Compute();                              //prints ("Kp/Ki/Kd/Distance/")
  
  //Serial.println("input: "+String(Input));// PID Compute
  //Serial.println("output: "+String(Output)); // for testing PID commands

  Serial.flush();
  Serial.print(Kp); Serial.print("|"); // this data is for the raspberry pi to read, make sure only these five lines print when running the graph
  Serial.print(Ki); Serial.print("|");
  Serial.print(Kd); Serial.print("|");
  Serial.print(String(range) + "|");
  Serial.println(String(Setpoint)); 
  
  setPwmDuty(Output);              // Sets the PWM duty cycle of the fan
}


int ReadDist() {                                  // Reads distance to ball, returns distance as integer in mm
  VL53L0X_RangingMeasurementData_t measure;

  

  lox.rangingTest(&measure, false);               // pass in 'true' to get debug data printout!

  if (measure.RangeStatus != 4) {                 // Phase failures have incorrect data
    //Serial.print("Distance (mm): ");           // Not used **unless troubleshooting sensor**
  } else {
    Serial.println(" out of range ");          // Not used **unless troubleshooting sensor**
  }
  int range = measure.RangeMilliMeter;            // Read Distance
  int real_range = 500 - range;
  return real_range;                                   // Return Distance

}

int getDataWithTimeout(unsigned long timeout) {
  unsigned long startTime = millis();
  int data = -1;
  bool dataReceived = false;
  while (millis() - startTime < timeout) {
    data = ReadDist();
    if (data != -1){
      dataReceived = true;
      break;
    }
  }

  if (dataReceived) {
    previousValidData = data;
  } else {
    data = previousValidData;
    
  }

  Input = int(data);
  return Input;
}


void readPots() {                       // Read Values from Potentiometers
  float potVal = analogRead(pPin);

  Kp = fmap(potVal, 0.0, 1023.0, 0.0, 2);  //INCLUDE MAP
  int switchVal = digitalRead(iSwitch);
  if (switchVal == HIGH) {                // if integral switch is off, Ki value is 0
    Ki = 0;  //INCLUDE MAP
  }
  else {            // if integral switch is on, assign I pot val to Ki
    potVal = analogRead(iPin);
    Ki = fmap(potVal, 0, 1023, 0, 1);  //INCLUDE MAP
  }
  switchVal = digitalRead(dSwitch);
  if (switchVal == HIGH) {                // if integral switch is off, Ki value is 0
    Kd = 0;  //INCLUDE MAP
  }
  else {            // if integral switch is on, assign I pot val to Ki
    potVal = analogRead(dPin);
    Kd = fmap(potVal, 0, 1023, 0, 1);  //INCLUDE MAP
  }
  myPID.SetTunings(Kp, Ki, Kd);                        // Set new tuning values
  myPID.SetSampleTime(sTime);                          // Set new sample time value
  //Serial.print(String(sTime) + "/");


}


float fmap(float x, float in_min, float in_max, float out_min, float out_max)
{
  return (x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min;
}
