import RPi.GPIO as GPIO
import time
import wiringpi
import threading
import os
import atexit

if os.geteuid() != 0:
    exit('You need to have root privileges to run this script.\nPlease try again, this time using \'sudo\'. Exiting.')

leftlight = 13
rightlight = 11
frontlight = 16
frontmode = 0
MODE_OFF = 0
MODE_HIGH = 1
MODE_LOW = 2
MODE_BLINK = 3
backlight = 15
wiringpi.wiringPiSetupGpio()
GPIO.setmode(GPIO.BOARD)
GPIO.setup(leftlight, GPIO.OUT)
GPIO.setup(rightlight, GPIO.OUT)
GPIO.setup(frontlight, GPIO.OUT)
GPIO.setup(backlight, GPIO.OUT)

lockpin = 18
wiringpi.pinMode(lockpin, wiringpi.GPIO.PWM_OUTPUT)
wiringpi.pwmSetMode(wiringpi.GPIO.PWM_MODE_MS)
wiringpi.pwmSetClock(192)
wiringpi.pwmSetRange(2000)

backlock = threading.Lock()
backthread = None
isRearBlinking = False

leftlock = threading.Lock()
leftthread = None
isLeftBlinking = False

rightlock = threading.Lock()
rightthread = None
isRightBlinking = False


def frontButtonPress():
    GPIO.output(frontlight, True)
    time.sleep(0.1)
    GPIO.output(frontlight, False)


def setFrontMode(mode):
    global frontmode
    if mode > MODE_BLINK or mode < MODE_OFF:
        return
    while frontmode != mode:
        frontButtonPress()
        if(frontmode == 3):
            frontmode = 0
        else:
            frontmode += 1


def startBlinkRear():
    global isRearBlinking, backthread
    if backthread is not None:
        return
    with backlock:
        isRearBlinking = True
    backthread = threading.Thread(target=blinkRearThread)
    backthread.start()


def blinkRearThread():
    while True:
        with backlock:
            if not isRearBlinking:
                break
        GPIO.output(backlight, True)
        time.sleep(0.1)
        with backlock:
            if not isRearBlinking:
                break
        GPIO.output(backlight, False)
        time.sleep(0.1)


def turnLeft():
    global isLeftBlinking, leftthread
    if leftthread is not None:
        return
    with leftlock:
        isLeftBlinking = True
    leftthread = threading.Thread(target=turnLeftThread)
    leftthread.start()


def turnLeftThread():
    while True:
        with leftlock:
            if not isLeftBlinking:
                break
        GPIO.output(leftlight, True)
        time.sleep(0.5)
        with leftlock:
            if not isLeftBlinking:
                break
        GPIO.output(leftlight, False)
        time.sleep(0.5)


def turnRight():
    global isRightBlinking, rightthread
    if rightthread is not None:
        return
    with rightlock:
        isRightBlinking = True
    rightthread = threading.Thread(target=turnRightThread)
    rightthread.start()


def turnRightThread():
    while True:
        with rightlock:
            if not isRightBlinking:
                break
        GPIO.output(rightlight, True)
        time.sleep(0.5)
        with rightlock:
            if not isRightBlinking:
                break
        GPIO.output(rightlight, False)
        time.sleep(0.5)


def doneLeftTurn():
    global isLeftBlinking, leftthread
    with leftlock:
        isLeftBlinking = False
    safejoin(leftthread)
    leftthread = None
    GPIO.output(leftlight, False)


def doneRightTurn():
    global isRightBlinking, rightthread
    with rightlock:
        isRightBlinking = False
    safejoin(rightthread)
    rightthread = None
    GPIO.output(rightlight, False)


def onRear():
    endBlinkRear(True)


def offRear():
    endBlinkRear(False)


def endBlinkRear(state):
    global isRearBlinking, backthread
    with backlock:
        isRearBlinking = False
    safejoin(backthread)
    backthread = None
    GPIO.output(backlight, state)


def lock():
    wiringpi.pwmWrite(lockpin, 55)


def unlock():
    wiringpi.pwmWrite(lockpin, 135)


def hazardLights():
    setFrontMode(MODE_BLINK)
    startBlinkRear()
    turnLeft()
    turnRight()


def safejoin(thread):
    if thread is not None:
        thread.join()


def offAll():
    setFrontMode(MODE_OFF)
    doneLeftTurn()
    doneRightTurn()
    offRear()


@atexit.register
def cleanup():
    offAll()
    GPIO.cleanup()
