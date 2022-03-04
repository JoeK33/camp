#!/usr/bin/env python
"""
Creates an HTTP server with basic auth and websocket communication.
"""
import argparse
import base64
import hashlib
import os
import time
import threading
import webbrowser
import random
import datetime
import camera_servo

try:
    import cStringIO as io
except ImportError:
    import io

import tornado.web
import tornado.websocket
from tornado.ioloop import PeriodicCallback

# Hashed password for comparison and a cookie for login cache
ROOT = os.path.normpath(os.path.dirname(__file__))
with open(os.path.join(ROOT, "password.txt")) as in_file:
    PASSWORD = in_file.read().strip()
COOKIE_NAME = "glamp"

recording = False

class IndexHandler(tornado.web.RequestHandler):

    def get(self):
        if args.require_login and not self.get_secure_cookie(COOKIE_NAME):
            self.redirect("/login")
        else:
            self.render("index.html", port=args.port)


class LoginHandler(tornado.web.RequestHandler):

    def get(self):
        self.render("login.html")

    def post(self):
        password = self.get_argument("password", "")
        if hashlib.sha512(password).hexdigest() == PASSWORD:
            self.set_secure_cookie(COOKIE_NAME, str(time.time()))
            self.redirect("/")
        else:
            time.sleep(1)
            self.redirect(u"/login?error")


class ErrorHandler(tornado.web.RequestHandler):
    def get(self):
        self.send_error(status_code=403)

class WebSocket(tornado.websocket.WebSocketHandler):
    recording = False
    lowLight = False
    def on_message(self, message):
        """Evaluates the function pointed to by json-rpc."""

        # Start an infinite loop when this is called
        if message == "read_camera":
            if not args.require_login or self.get_secure_cookie(COOKIE_NAME):
                self.camera_loop = PeriodicCallback(self.loop, 33)
                self.camera_loop.start()
            else:
                print("Unauthenticated websocket request")

        elif message == "toggle_low_light":
            print("toggle low light")
            WebSocket.lowLight = not WebSocket.lowLight
            if (WebSocket.lowLight) :
                camera.exposure_mode = 'night'
            else:
                camera.exposure_mode = 'auto'

        elif message == "take_photo" and not WebSocket.recording:
            # not sure if works for usb camera
            print("take photo")
            res = camera.resolution
            camera.resolution = (2592, 1944)
            camera.capture('photos/rov_' + str(datetime.datetime.now()) + '.png')
            camera.resolution = res

        elif message == "res_down" and not WebSocket.recording:
            print("res down")
            res = camera.resolution
            possible_res = list(resolutions)
            index = possible_res.index(str(res))
            if index > 0:
                if args.use_usb:
                    w, h = possible_res[index - 1]
                    camera.set(3, w)
                    camera.set(4, h)
                else:
                    camera.resolution = possible_res[index - 1]

        elif message == "res_up" and not WebSocket.recording:
            print("res up")
            res = camera.resolution
            possible_res = list(resolutions)
            index = possible_res.index(str(res))
            if index < len(possible_res) - 1:
                if args.use_usb:
                    w, h = possible_res[index + 1]
                    camera.set(3, w)
                    camera.set(4, h)
                else:
                    camera.resolution = possible_res[index + 1]

        elif message == "start_record":
            # not sure if works for usb camera
            print("start recording")
            if not WebSocket.recording:
                camera.start_recording('videos/rov_' + str(datetime.datetime.now()) + '.h264')
                WebSocket.recording = True

        elif message == "stop_record":
            # not sure if works for usb camera
            print("stop recording")
            if WebSocket.recording:
                camera.stop_recording()
                WebSocket.recording = False

        elif message == "camera_down":
            print("camera down")
            camera_servo.TiltServo.tilt_down()

        elif message == "camera_up":
            print("camera up")
            camera_servo.TiltServo.tilt_up()

        elif message == "reboot":
            print("reboot")
            os.system('sudo shutdown -r now')

        elif message == "shutdown":
            print("shutting down")
            os.system('sudo shutdown -h now')

        else:
            print("Unsupported function: " + message)

    def loop(self):
        """Sends camera images in an infinite loop."""
        try:
            sio = io.BytesIO()  # for Python3
        except AttributeError:
            sio = io.StringIO()  # for Python2

        if args.use_usb:
            _, frame = camera.read()
            img = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
            img.save(sio, "JPEG")
        else:
            camera.capture(sio, "jpeg", use_video_port=True)

        ui_dict = {}

        ui_dict["cameraAngle"] = str(camera_servo.getServoValue()) + " %"
        ui_dict["resolution"] = str(camera.resolution)

        if WebSocket.recording:
            ui_dict["isRecording"] = "Recording"
        else:
            ui_dict["isRecording"] = "Not Recording"

        if WebSocket.lowLight:
            ui_dict["isLowLight"] = "Low Light On"
        else:
            ui_dict["isLowLight"] = "Low Light Off"

        try:
            ui_dict["camera"] = str(base64.b64encode(sio.getvalue()))
            self.write_message(ui_dict)
        except tornado.websocket.WebSocketClosedError:
            self.camera_loop.stop()

parser = argparse.ArgumentParser(description="Starts a webserver that "
                                             "connects to a webcam.")
parser.add_argument("--port", type=int, default=8000, help="The "
                                                           "port on which to serve the website.")
parser.add_argument("--resolution", type=str, default="854x480", help="The "
                                                                  "video resolution. Can be 426x240, 640x480, 854x480c 1042x576, 1280x720")
parser.add_argument("--require-login", action="store_true", help="Require "
                                                                 "a password to log in to webserver.")
parser.add_argument("--use-usb", action="store_true", help="Use a USB "
                                                           "webcam instead of the standard Pi camera.")
parser.add_argument("--usb-id", type=int, default=0, help="The "
                                                          "usb camera number to display")
args = parser.parse_args()

if args.use_usb:
    import cv2
    from PIL import Image

    camera = cv2.VideoCapture(args.usb_id)
else:
    import picamera

    camera = picamera.PiCamera()
    camera.start_preview()

resolutions = {"426x240": (426, 240), "640x480": (640, 480), "854x480": (854, 480), "1024x576": (1024, 576), "1280x720": (1280, 720)}
if args.resolution in resolutions:
    if args.use_usb:
        w, h = resolutions[args.resolution]
        camera.set(3, w)
        camera.set(4, h)
    else:
        camera.resolution = resolutions[args.resolution]
else:
    raise Exception("%s not in resolution options." % args.resolution)

handlers = [(r"/", IndexHandler), (r"/login", LoginHandler),
            (r"/websocket", WebSocket),
            (r"/static/password.txt", ErrorHandler),
            (r'/static/(.*)', tornado.web.StaticFileHandler, {'path': ROOT})]
application = tornado.web.Application(handlers, cookie_secret=PASSWORD)
application.listen(args.port)

webbrowser.open("http://localhost:%d/" % args.port, new=2)

tornado.ioloop.IOLoop.instance().start()
