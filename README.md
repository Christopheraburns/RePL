Project RePL

What is this project?
This project is meant to demonstrate the power of AI-as-a-service.  It also highlights the convergence of Machine Learning,
Machine Intelligence, Robotics and Cloud Computing.

Why the name RePL?

In developer parlance, a REPL is a Read Evaluaton Process Loop - the mechanism in some languages to allow you to write code
and receive instant processing and feedback.  iPython is a perfect example.  Ruby, Erlang and several other languages that have
REPLS.  In the case of this project, RePL (not the small 'e') ALSO stands of Re-kognition (AWS Rekognition) P-olly (AWS Polly)
L-ex (AWS Lex) and will leverage those three services as well as AWS Machine learning to demonstrate the power of AI-as-a-service.


Why Python?

I don't like dynamically typed languages - hard to grow a large code base, hard to debug (visually)

However, the good stuff about Python outweighs the bad stuff.

Language	Robotics	NLP	   Computer Vision	Raspberry PI	Data Mining	   GUI	 Backend Code	AWS SDK
---------   ------	    ---	   ---------------	------------	-----------	   ---	 ------------	-------
Python		yes			yes		    yes			    yes	        yes		       yes   yes            yes


In addition to the above libraries and modules there is wealth of literature, tutorials and sample code written in python that
will help pay down the project's technical debt.  I am going to try to use python exclusively until I have a compelling
reason to use something else. For instance, some computer vision tasks will most likely need to be written in C for CUDA, unless the Python CUDA libraries
prove powerful enough.


Directory Structure:

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