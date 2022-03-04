from gpiozero import Servo
from gpiozero.pins.pigpio import PiGPIOFactory
import keyboard

factory = PiGPIOFactory()

class TiltServo:
    tilt_servo = Servo(21, min_pulse_width = 0.5/1000, max_pulse_width = 2.5/1000, pin_factory = factory)

    camera_servo_position = 0.0

    def tilt_down() :
        print("Tilt camera down")
        TiltServo.camera_servo_position -= 0.02
        if TiltServo.camera_servo_position < -1:
            TiltServo.camera_servo_position = -1
        TiltServo.move_servo()

    def tilt_up() :
        print("Tilt camera up")
        TiltServo.camera_servo_position += 0.02
        if TiltServo.camera_servo_position > 1:
            TiltServo.camera_servo_position = 1
        TiltServo.move_servo()

        ### tilt between -1 (down) and 1 (up)
    def set_tilt(tilt) :
        print("Tilt camera down")
        TiltServo.camera_servo_position = tilt
        if TiltServo.camera_servo_position < -1:
            TiltServo.camera_servo_position = -1
        if TiltServo.camera_servo_position > 1:
            TiltServo.camera_servo_position = 1
        TiltServo.move_servo()

    def move_servo() :
        print("Moving camera")
        servo_position = 0

        # negative makes camera look up. camera mount makes looking down need less range of motion
        if TiltServo.camera_servo_position > 0:
            servo_position = - TiltServo.camera_servo_position
        elif TiltServo.camera_servo_position < 0:
            servo_position = - (TiltServo.camera_servo_position / 2)
        print(TiltServo.camera_servo_position)

        TiltServo.tilt_servo.value = servo_position


def getServoValue():
    return int(TiltServo.camera_servo_position * 100)