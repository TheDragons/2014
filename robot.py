try:
    import wpilib
except:
    import pyfrc.wpilib as wpilib
import socket
import sys
import time
#from Functions import *

#   Notes for transition to Comp Bot
#    - Adjust code for 3 CIM DT
#    - Re-calculate Bias for 3CIM DT
#    - 

stick = wpilib.Joystick(1)
spareJoy = wpilib.Joystick(2)
secretjoy = wpilib.Joystick(3)
cop = wpilib.Joystick(4)

l1 = wpilib.Talon(2)
l2 = wpilib.Talon(4)
l3 = wpilib.Talon(6)
r1 = wpilib.Talon(1)
r2 = wpilib.Talon(3)
r3 = wpilib.Talon(5)

roller = wpilib.Talon(8)
cocker = wpilib.Talon(7)

lights = wpilib.Relay(2)

spitime = wpilib.Timer()
autotime = wpilib.Timer()
rolltime = wpilib.Timer()
safetime = wpilib.Timer()
autonTimer = wpilib.Timer()

ultra = wpilib.AnalogChannel(1)
pressure = wpilib.AnalogChannel(2)

dogin  = wpilib.Solenoid(5)
dogout = wpilib.Solenoid(6)

armin  = wpilib.Solenoid(3)
armout = wpilib.Solenoid(4)

shiftup = wpilib.Solenoid(1)
shiftdn = wpilib.Solenoid(2)

enc1 = wpilib.Encoder(2,3,False)
enc2 = wpilib.Encoder(4,5,True)
kicken = wpilib.Encoder(6,7)

kickSwitch = wpilib.DigitalInput(8)
ballDector = wpilib.DigitalInput(10)
comp = wpilib.Compressor(1,1)

ds = wpilib.DriverStationLCD.GetInstance()

#-----------------VARIABLES---------------

def CheckRestart():
        if stick.GetRawButton(12):
                raise RuntimeError("reboot")

class MyRobot(wpilib.SimpleRobot):
#        def __init__(self):
#                super().__init__()
#                self.functions = Functions()
        def Disabled(self):
                while self.IsDisabled():
                        if (secretjoy.GetRawButton(3) == True):
                                sys.exit()
                        
                        CheckRestart()
                        wpilib.Wait(0.01)

        def Autonomous(self):
                self.GetWatchdog().SetEnabled(False)
                autonTimer.Reset()
                autonTimer.Start()
                
                ds.Clear()

                enc1.Start()
                enc1.Reset()

                enc2.Start()
                enc2.Reset()

            #Auton-setpoint changes how far forward the robot goesS
                setpoint = 2450#2000#1750 midland
                gain = 1000

                go = True
                doggie = False
                
                SetRoller = 0.000
                CockRate = 620
                SetCock = 0.00
                CockGain = 3000
                CockPositionRate = 0.000
                cocked = True
                diff = 0.000
                window = 0.05
                i = 0
                
                autotime.Start()
                autotime.Reset()
                autotime.Stop()
                
            #---------This code uses UDP to get info from the vision processing
                noConnect = False
                
                print("starting udp code")
                
     
                message = ""
                
                UDP_IP = "0.0.0.0"#"10.12.43.5"
                UDP_PORT = 1130

                sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                sock.bind((UDP_IP, UDP_PORT))
                sock.settimeout(0.01)

                    
                print("binded ports")
                
                #--------------looking for HotGoal
                InComingIP = ""
                t0 = time.time()
                
                hotGoal = False
                
                print("about to loop")
                
                print(str(noConnect))
                status = ""
                autonWait = 3
                while self.IsAutonomous() and self.IsEnabled():
                        try:
                            data, addr = sock.recvfrom(1024)
    
                            InComingIP = addr[0]
                        
                            #print (InComingIP)
                            
                            if ("10.12.43" in InComingIP):
                                message =  (data.decode("utf-8"))
                                hotGoal = (message == "True")   
                        except:
                            pass
                        
                        if hotGoal:
                            autonWait = 1
                            
                        
                        i += 1
                        
                        if (i%5 == 0):
                            print (str(i))
                            print (status)
                            
                        lside = (-0.4 * 0.99)
                        rside = (0.4 * 1.00000)
                        
                    #    if (abs(enc2.GetDistance()) > setpoint):
                    #            lside = 0
                                
                        if (abs(enc1.GetDistance()) > setpoint):
                                rside = 0.01
                                lside = 0.01
                                status = "driving foward"
                        if ((lside == 0.01) and (rside == 0.01)):
                                armin.Set(False)
                                armout.Set(True)
                                SetRoller = -0.3
                                autotime.Start()
                                status = "reached position"

                        if ((autotime.Get() > autonWait) and (autotime.Get() < (autonWait + .5))):
                                doggie = True
                                SetRoller = 0.000
                                status = "Kicked"
                                print(str(autonTimer.Get()))

                    #---------------- Cock control

                        kickLimit = not(kickSwitch.Get())
                                
                        if ((kickLimit == False) and (abs(kicken.GetRate()) <= window)):
                                cocked = False
                                safetime.Start()
                                
                        if ((cocked == False) and (safetime.Get() > 1) and (safetime.Get() < 8)):
                                doggie = False
                                diff = (-1*(kicken.GetRate() - CockRate)/CockGain)
                                CockPositionRate = CockPositionRate + diff
                                SetCock = CockPositionRate
                                status = "reloading"

                        if (kickLimit):
                                cocked = True
                                CockPositionRate = 0.00
                                safetime.Reset()
                                safetime.Stop()
                #----------------------Motor Set and soli
                        dogin.Set(not doggie)
                        dogout.Set(doggie)
                        
                        l1.Set(lside)
                        r1.Set(rside)
                        l2.Set(lside)
                        r2.Set(rside)
                        l3.Set(lside)
                        r3.Set(rside)
                        
                        cocker.Set(SetCock)
                        roller.Set(SetRoller)
                        
                        ds.Clear()
                        
                        ds.Print(ds.Line(0), 1, "enc1: " + str(enc1.GetDistance()))
                        ds.Print(ds.Line(1), 1, "enc2: " + str(enc2.GetDistance()))
                        ds.Print(ds.Line(2), 1, "KickRate: " + str(kicken.GetRate()))
                        ds.Print(ds.Line(3), 1, "kickSwitch: " + str(kickLimit))
                        ds.Print(ds.Line(4), 1, "SetLauncher: " + str(SetCock))
                        ds.Print(ds.Line(5), 1, "Hot Goal:" + str(autonWait))
                        
                        ds.UpdateLCD()
                #----------------zero me out\
                        SetCock = 0.0000000000000000000000
                        SetRoller = 0.00000000
                sock.close() 

        def OperatorControl(self):
                dog = self.GetWatchdog()
                dog.SetEnabled(False)
                
                ds.Clear()
                enc1.Start()
                enc1.Reset()
                enc2.Start()
                enc2.Reset()
                kicken.Start()
                kicken.Reset()

                safetime.Reset()
                safetime.Stop()
                
                comp.Start()

                spitime.Start()
                
                stick8 = 0
                stick8fall = False
                stick1 = 0
                stick1fall = False

                SetRoller = 0.000
                CockRate = 600
                SetCock = 0.00
                CockGain = 3000
                CockPositionRate = 0.000
                cocked = True
                diff = 0.000
                window = 0.05

                joyRY = 0
                dtGain = 0.05
                setR = 0
                setL = 0

                recorded = 0
                multiplier = 0.75
                lowvolt = 0
                setter = 0
                lastenc = enc1.GetDistance()

                setpoint = 1000
                gain = 750

                setrate = 100
                kgain = 100
                
                #foward
                lBias = 0.99#0.93226#0.775 #
                #backward
                rBias = 1.0 #0.95896

                flippy = False
                roll = False

                shift = False

                spit = False

                rside = 0.0
                lside = 0.0
                joyY = 0.0
                joyX = 0.0
                compOn = True

                doggie = False
                arm = True
                overide = False
                maxPressVolt = 3.9
                while self.IsOperatorControl() and self.IsEnabled():
                        dog.Feed()
                        CheckRestart()

                        vpi = (4.982/512)
                        ultraInches = ((ultra.GetVoltage())/vpi)
                        ultraFeet   = ((ultraInches)/12)
                        
                        kickLimit = not(kickSwitch.Get())
        #---------------- Button clauses

                        if (spareJoy.GetRawButton(2) == 1):
                                flippy = False
                        elif (secretjoy.GetRawButton(2) == 1):
                                flippy = True

                        if (flippy == True):
                                #multiplier = -0.75
                                rside = spareJoy.GetRawAxis(2)*-1#stick.GetRawAxis(2)*-1#(((joyY)+(joyX))*-1)
                                lside = secretjoy.GetRawAxis(2)#stick.GetRawAxis(5)#(((joyY)-(joyX)))
                        elif (flippy == False):
                                #multiplier = 0.75
                                rside = secretjoy.GetRawAxis(2)#stick.GetRawAxis(5)#(((joyY)-(joyX)))
                                lside = spareJoy.GetRawAxis(2)*-1#stick.GetRawAxis(2)*-1#(((joyY)+(joyX))*-1)

                        if (cop.GetRawButton(7) == 1):
                                doggie = False
                        elif (cop.GetRawButton(6) == 1):
                                doggie = True
                                kickLimit = True

                        if (stick.GetRawButton(6) == 1):
                                shift = True
                        elif (stick.GetRawButton(5) == 1):
                                shift = False

                        if (cop.GetRawAxis(2) < -0.3):
                                arm = False
                                spit = True
                                spitime.Reset()
                        elif (cop.GetRawAxis(2) > 0.3):
                                arm = True

                        if ((spit == True) and (spitime.Get() < 0.5)):
                                joyRY = -0.4
                                      
                #       if ((stick.GetRawButton(8) == 0) & (stick8 == 1)):
                #               stick8fall = not stick8fall
                                
                        
                #       if (stick8fall):
                #               comp.Start()
                #       else:
                #               comp.Stop()
                        

                        if (stick.GetRawButton(3) == 1):
                                enc1.Reset()
                                
        #---------------- Analog Motor controls
                                
                        joyY = stick.GetRawAxis(2)
                        joyX = stick.GetRawAxis(1)
                        SetCock = stick.GetRawAxis(3)

                        #roller controll
                        if (cop.GetRawButton(10) == 1):
                                joyRY = -1

                        if (cop.GetRawButton(11) == 1):
                                roll = True

                        #
                        if (ballDector.Get()):
                                lights.Set(wpilib.Relay.kReverse)
                        else:
                                lights.Set(wpilib.Relay.kForward)
                                
                        #sets the roller to roll for a second when we move the kicker out
                        if (roll == True):
                                rolltime.Start()
                                if (rolltime.Get() < 1):
                                        joyRY = 1
                                elif (rolltime.Get() > 1):
                                        roll = False
                                        rolltime.Reset()
                                        rolltime.Stop()                        
                        
                                
                        ##This sets our dead band on the joystick
                        if ((rside <= dtGain*-1) or (rside >= dtGain)):
                                setR = (rside/abs(rside))*((1/(1-dtGain))*(abs(rside)-dtGain))
                                
                        if ((lside <= dtGain*-1) or (lside >= dtGain)):
                                setL = (lside/abs(lside))*((1/(1-dtGain))*(abs(lside)-dtGain))

                        ##Set biased
                        if (setR < 0):
                                setR = setR * rBias
                        if (setR > 0):
                                setR = setR * 1
                        
                        if (setL < 0):
                                setL = setL * 1
                        if (setL > 0):
                                setL = setL * lBias
                        
        #---------------- Cock control
                                
                        if ((kickLimit == False) and (abs(kicken.GetRate()) <= window)):
                                cocked = False
                                safetime.Start()
                                
                        if ((cocked == False) and (safetime.Get() > 1) and (safetime.Get() < 8)):
                                doggie = False
                                diff = (-1*(kicken.GetRate() - CockRate)/CockGain)
                                CockPositionRate = CockPositionRate + diff
                                SetCock = CockPositionRate
                                
                        

                        if (kickLimit):
                                cocked = True
                                CockPositionRate = 0
                                safetime.Reset()
                                safetime.Stop()
                                
        #---------------- Solonoid control
                        
                        dogin.Set(not doggie)
                        dogout.Set(doggie)
                        
                        shiftup.Set(not shift)
                        shiftdn.Set(shift)

                        armout.Set(not(arm))
                        armin.Set(arm)
        #---------------Compressor Controll
        
                        if (pressure.GetVoltage() > maxPressVolt) and (overide == False):
                            compOn = False
                            maxPressVolt = 3.0
                        if (pressure.GetVoltage() < 2.5) and (overide == False):
                            compOn = True
                            
                        if (cop.GetRawButton(8) == 1):
                                compOn = True
                                overide = True
                        if (cop.GetRawButton(9) == 1):
                                compOn = False
                                overide = True
                        if (cop.GetRawButton(7)):
                            overide = False
        #---------------- Updating the boolean values for the toggle functions
                        stick1 = stick.GetRawButton(1)
                        stick8 = stick.GetRawButton(8)
                        
        #---------------- Motor control
                        if (SetCock < 0):
                                SetCock = 0
                        if (SetCock > 1):
                                SetCock = 1
                        
                        if (secretjoy.GetRawButton(8) == 1):
                                SetCock = -1
                        elif (secretjoy.GetRawButton(9) == 1):
                                SetCock = 1
                        
                        setL = setL#*0.75
                        setR = setR#*0.75
                        
                        #if (spareJoy.GetRawButton(7)):
                        #    setL = 1
                        #    setR = 1
                        #if (spareJoy.GetRawButton(8)):
                        #    setL = -1
                        #    setR = -1
                            
                        l1.Set(setL)
                        l2.Set(setL)
                        l3.Set(setL)
                        r1.Set(setR)
                        r2.Set(setR)
                        r3.Set(setR)
                        
                        cocker.Set(SetCock)

                        roller.Set(joyRY)

                        if compOn:
                            comp.Start()
                        else:
                            comp.Stop()
        #-------------- Driverstaion lcd display
                        ds.Clear()
                        
                        ds.Print(ds.Line(0), 1, "Cat Value: " + str(SetCock))
                        ds.Print(ds.Line(1), 1, "setR: " + str(setR))
                        ds.Print(ds.Line(2), 1, "setL: " + str(setL))
                        ds.Print(ds.Line(3), 1, "Pressure Voltage: " + str(pressure.GetVoltage()))
                        ds.Print(ds.Line(4), 1, "compressor on: " + str(compOn))
                        ds.Print(ds.Line(5), 1, "Ball Sense: " + str(ballDector.Get()))
                        
                        ds.UpdateLCD()
        #---------------------zero cause
                        setR = 0.000000
                        setL = 0.000000
                        joyRY = 0.000000
                        SetCock = 0.000000
                        pastCompOn = compOn
                        wpilib.Wait(0.04)

def run():
        robot = MyRobot()
        robot.StartCompetition()
