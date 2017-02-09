!!!!!   IMPORTANT   !!!!!

This will not be a comprehensive list of hardware that will work with this project.  By it's very nature - the creator can use
many different types of hardware.  This is simply a list of hardware used in this instance.

*Note this list will most likely be out of date or obsolete as components are constantly being replaced and added.



Component                   Hardware Choice                     URL                                         App Cost
-------------------         ----------------------------        --------------------------------------      --------
Body/Frame                  Meccano Meccanoid G15               http://www.meccano.com/meccanoid-about      $100   
Body/Frame                  Meccano Meccasaur                   http://tinyurl.com/jj9d64h                  $50
Body/Frame                  Makeblock Starter Robot kit         http://tinyurl.com/jz5sy6a                  $120
Front Wheels                Meccano Meccanoid G15               http://www.meccano.com/meccanoid-about      
Rear Treads/DC Motors       Makeblock Starter Robot kit         http://tinyurl.com/jz5sy6a
Controller Unit             Raspberry PI 3                      https://www.adafruit.com/products/3055      $40
Half sized Breadboard       Any bread board with side terminals https://www.adafruit.com/products/64        $5
Jumper Wires                Female to male, or male to male     http://tinyurl.com/j29jumz                  $10
WebCam                      Any HD, widescreen USB webcam       http://tinyurl.com/zx4dp2l                  $70
Neck servos                 MallofUsa 2 DoF kit                 


Notes on Servo Motors
---------------------

    Servos are not DC motors!
    Servos require PWM (PulseWidth Modulation) from the Pi
    Servos only move 180 degrees
    Use a 50hz Control Signal (Frequency)
    Most* Servos are fully left with around 1 millisecond pulsewidth
    Most* Servos are in the middle position with a 1.5 millisecond pulsewidth
    Most* Servos are fully right with around a 2 millisecond pulsewidth
    
        Take note:
        Hertz(Period) = 1/Frequency
        Given a 50hz signal, the period of the signal is:
            Hertz(Period) = 1/Frequency = 1/50 = .02 = 20 milliseconds
        To be in the full left position we would want a pulsewidth of 1 millisecond
        1 millisecond would be a Dutycycle of 5 percent
            .05X20 (millisecond) = 1 millisecond
        *So for full left we would want a DutyCycle of 5 percent on a 50Hz signal
        
        To be in the middle position, we would want a pulsewidth of 1.5 millisecond
        1.5 Millisecond would be a dutycycle of 7.5 on a 50Hz signal
            .075X20 = 1.5 Millisecond
        *So for middle position we would want a DutyCycle of 7.5 percent on a 50Hz signal
        
        Finally, to be in the full right position we would want a pulsewidth of 2 millisecond
        2 Millisecond would be a dutycycle of 10 on a 50Hz signal
            .10X20 = 2.0 