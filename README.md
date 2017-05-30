[//]: # (Image References)

[image1]: ./images/repl_front.JPG "RePL"
[image2]: ./images/RePLDesign_1.png "RePL Conceptual model"
[image3]: ./images/repl_backside.JPG "RePL nav unit plaecement"
[image4]: ./images/repl_arm.JPG "RePL arm"
[image5]: ./images/repl_subsystems.JPG "RePL Subsystems"
[image6]: ./images/coreI5.JPG "Intel powered cortex"
[image7]: ./images/repl_lcd_mic_speaker.JPG "Robot I/O"

**Project RePL**

![alt text][image1]

What is this project?
This project is meant to demonstrate the power of AI-as-a-service.  It also highlights the convergence of Machine Learning,
Machine Intelligence, Robotics and Cloud Computing.  RePL is a prototype.  A substrate for me to create Robot source 
code based on my own Autonomous navigation system as well as ROS.  The current body is actually a combination of parts 
from 3 different [Meccano](http://www.meccano.com/)robot toys (erstwhile children’s gifts collecting dust)  My plan is construct a professional 
grade robot approximately 4’ tall by means of 3D printing and traditional manufacturing means (subtractive mfg).  
In addition to being a creative outlet for me to exercise my mechatronics, software development and cloud computing 
skills, the robot will accompany me as a personal assistant at workshops, bootcamps and other training events to 
showcase the “art of the possible”.    I hope to write about the interactions between her and people we meet at stores, 
events, offices, etc.

**Why the name RePL?**

The word “RePL” is an acronym-homograph.  In developer parlance, a REPL is a Read Evaluaton Process Loop - 
the mechanism in some languages to allow you to write code and receive instant processing and feedback.  
iPython is a perfect example.  Ruby, Erlang and several other languages have REPLS.  
RePL is also meant to represent [<b>Re</b>-kognition](https://aws.amazon.com/rekognition/), [<b>P</b>-olly](https://aws.amazon.com/polly/) 
and [<b>L</b>-ex](https://aws.amazon.com/lex/) -the AWS services that give the Robot 
her superpowers.


**Why Python?**

I don't normally like dynamically typed languages - however, python has too much to offer with this project

However, the good stuff about Python outweighs the bad stuff.

| Robotics |  NLP   | Computer Vision | Raspberry PI |	Data Mining	| GUI |	Backend	|AWS SDK | ML  |
| -------- | ------ | --------------- | ------------ |	-----------	| --- |	-------	|------- | --- |
|  YES	   |  YES   |		YES       |	    YES	     |      YES	    | YES |    YES  |  YES   | YES |
|  ROS     | KITT.AI|     OpenCV      |     RPi      |  matplotlib  | [yes](https://wiki.python.org/moin/GuiProgramming)| Yes |  Boto3 |  numpy |

In addition to the above libraries and modules there is wealth of literature, tutorials and sample code written in python that
will help pay down the project's technical debt.  I am going to try to use python exclusively until I have a compelling
reason to use something else i.e [cython](http://cython.org/)


**Conceptual architecture overview**

The following is a brief overview of how I constructed the Robot.
(The Navigation section in gray is currently underdevelopment)


![alt text][image2]

RePL uses an Intel Core i5 system board as the “Cortex” or control center. (The system board was pulled from a Dell Latitude)
She will use an [NVIDIA Jetson TX2](http://www.nvidia.com/object/embedded-systems-dev-kits-modules.html) for navigation. RePL v.2 will use a NUC computer.  The robot has a “centaur” design (Figure 1.1) to carry the i5 system board, 
the NVidia Jetson (with system board) as well as 2 6v batteries and 2 12V batteries. The2 12V chained (24v) batteries will power the Jetson chip.
The arms (8 servos total) have one dedicated 6v SLA battery stored in one of the “legs”.  The DC motors also have a dedicated 6V SLA battery, stored in the other “leg”.
The i5 core still uses the battery that came with the Laptop.  The Rpi3 and Arduino are both powered via USB 5v from the i5 system board.

Figure 1.1
![alt text][image3]


The Cortex has dual network connections.  One NIC is connected to the internet to access the AWS cloud services for voice 
(Polly) and image recognition (Rekognition).  The other NIC is dedicated to an onboard network used exclusively by the MQTT system.  
The MQTT hosts run on the i5 core.  To make arm movements a message is sent to the REPL_MF queue and an RPi3 picks up the message.  
The RPi3 controls the arm movement via PWM to servos (Figure 1.2).    An Arduino YUN (figure 1.3)  is the access point to the onboard network.  
The YUN also controls DC motor functions as well as some sensor input (Ultrasonic and Motion Sensing)

Figure 1.2
![alt text][image3]


Each arm has 4 servos giving the arms 4 DOF. (Figure 1.3) The arm can be rotated or raised at the shoulder.   This is a poorly implemented 
shoulder. I have a design for a ball socket for v.2.  RePL has elbows for bending her arms and also has wrists to rotate her hands.
Her left arm is currently a gripper (DC powered).  Her right hand is not functional but I have a design for two functional hands in v.2
Low end servos are currently being used.  [Dynamixel](http://www.robotis.us/dynamixel/) servos will be incorporate into this 
version soon to further develop kinematics.

Figure 1.3
![alt text][image4]


**Subsystems**

Mounted backpack style are a [Rpi3](https://www.raspberrypi.org/products/raspberry-pi-3-model-b/) and an 
[Arduino Yun](https://www.arduino.cc/en/Main/ArduinoBoardYun). (Figure 1.4) The Rpi leverages an [AdaFruit PWM Hat](https://www.adafruit.com/product/815)
and the Yun uses a [Motor Shield](https://www.adafruit.com/product/1438) - you could build your own h-bridge for $5, but for $20 this is 
better option.

Figure 1.4 (Subsytems are slightly obscured by wiring)
![alt text][image5]

**Cortex**
The i5 Core i5 acts as the cortex. (see architecture diagram above) Today, all video and sound IO (mic, speakers, web cam) 
route through the i5 core. When the [NVIDIA Jetson TX2](http://www.nvidia.com/object/embedded-systems-dev-kits-modules.html) is incorporated the i5 core will only manage sound and object labelling and scene detection.  
The [NVIDIA Jetson TX2](http://www.nvidia.com/object/embedded-systems-dev-kits-modules.html) will handle obstacle avoidance and all other navigation duties.
The i5 core system board in at the back to robot (figure 1.5), standing up on end assist with cooling and
to keep the board protected from shortages (several RPis and Yuns died while building RePL).

Figure 1.5
![alt text][image6]

**Subsytem I/O**
Figure 1.7
The RPi3 has a dedicated 7” LCD mounted on the front of RePL. I use this today to monitor MQTT activity but will soon 
use it to show images relevant to tasks - for instance, maps, images of events that we attended, places visited, etc. 
Currently there is only a single uni-direction microphone.  I am working on a system that will use 4 – 8 uni-direction mics 
so she can determine the direction sounds are come from. A single speaker is used when she speaks.

Figure 1.7
![alt text][image7]



**GIT Repositories**
RePL uses three repositories:
The current repo:
[Cortex](https://github.com/Christopheraburns/RePL_Cortex)

A repo for controlling Servos
[Motor_Functions](https://github.com/Christopheraburns/RePL_MotorFunctions)

A repo for controlling dc motors (Arduino Sketches)
[Propulsion Systems](https://github.com/Christopheraburns/REPL_propulsion)


**Current repo directory structure**:

audio: working directory for .ogg files from Polly as well as some autoresponder files.
images: working directory for .png and video files taken from the camera.
docs: directory for dependency information, hardware descriptions, misc files, program notes, todo lists, etc.

    dependencies.txt        This is a list of (software) dependencies that are required to operate a robot


    __main__.py:  The Application entrypoint. Asserts that sys.args variables are present and correct.
            Loads SnowBoy and Speech Recognition libraries, creates a log file and passes operation flow to the cortex
            when a command is detected.

    _snowboydetect.so
    snowboydetect.py: These two files are REQUIRED for snowboy to function - no need to alter them!

    flac-linux-x86
    flac-linux-x86_64
    flac-mac:               This is a converter used by the Speech Recognition libraries (NOT AWS Rekognition)

    autoresponder.json:     This file will most likely evolve into a Database.  Today it will be used to store one or more 
                            responses to commands spoken to RePL.  The responder engine will take all available commands 
                            and offer a random response.


    cortex.py:              This file manages all interaction with the external environment and the Robot's senses. 
                            i.e. Motorfunctions, Speech, Vision, propulsion, etc.
    computerspeech.py:      This file will control and manage calls to Polly and outputting Polly responses to the speaker.
    computerVision.py:      This file will control and manage access to the camera.

    help:                   This is the help file that is delivered to the console if -h or -help is added to the sys.args

    JOINTMAP:               This file allows for Robot to be wired differently - as long as the JOINTMAP file is synced 
                            with the wiring harness.
     
    log.py                  This file is a wrapper to the python Logger class. It adds a datetime stamp to all entries and can 
                            optionally write to the console in addition to the log file.
                        
    motorfunctions.py       This file is used by the Cortex module to coordinate verbal commands from humans into function calls
                            for the servo motors.
                        
    REPL.pmdl               This file is the "Personal Model" file for Snowboy.  In order to change the wake word, go to 
                            https://snowboy.kitt.ai/ and create a new keyword file.
                        
    speechrecognition.py    This file is the primary module for converting verbal [human] commands into text. It s