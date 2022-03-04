/*global $, WebSocket, console, window, document*/
"use strict";

/**
 * Connects to Pi server and receives video data.
 */
var client = {

    // Connects to Pi via websocket
    connect: function (port) {
        var self = this,
         video = document.getElementById("video"),
         takePhotoButton = document.getElementById("takePhoto"),
         resDownButton = document.getElementById("resDown"),
         resolution = document.getElementById("resolution"),
         resUpButton = document.getElementById("resUp"),
         startRecordingButton = document.getElementById("startRecording"),
         isRecording = document.getElementById("isRecording"),
         stopRecordingButton = document.getElementById("stopRecording"),
         cameraAngle = document.getElementById("cameraAngle"),
         lowLightButton = document.getElementById("lowLightToggle"),
         isLowLight = document.getElementById("isLowLight"),
         rebootButton = document.getElementById("reboot"),
         shutdownButton = document.getElementById("shutdown");

        this.socket = new WebSocket("ws://" + window.location.hostname + ":" + port + "/websocket");

        // Request the video stream once connected
        this.socket.onopen = function () {
            console.log("Connected!");

            self.readCamera();

            takePhotoButton.onclick = function() {
                   self.takePhoto();
            }

            resDownButton.onclick = function() {
                   self.resDown();
            }

            resUpButton.onclick = function() {
                   self.resUp();
            }

            startRecordingButton.onclick = function() {
                   self.startRecord();
            }

            stopRecordingButton.onclick = function() {
                   self.stopRecord();
            }

            lowLightButton.onclick = function() {
                   self.toggleLowLight();
            }

            rebootButton.onclick = function() {
                   self.reboot();
            }

            shutdownButton.onclick = function() {
                   self.shutdown();
            }

            document.addEventListener('keydown', function(event){
            console.log(event.keyCode)

                if (event.keyCode == 107) { // +
                    self.tiltCameraUp();
                }

                if (event.keyCode == 109) { // -
                    self.tiltCameraDown();
                }

            } );
        };

        this.socket.onmessage = function (messageEvent) {
            var info = JSON.parse(messageEvent.data);
            console.log(info)
        	var vidSrcSuffix = info.camera.substring(2, info.camera.length - 1);
            video.src = "data:image/jpeg;base64," + vidSrcSuffix;
            cameraAngle.innerHTML = "Camera Angle: " + String(info.cameraAngle);
            resolution.innerHTML = String(info.resolution)
            isRecording.innerHTML = info.isRecording
            isLowLight.innerHTML = info.isLowLight
        };
    },

    // Requests video stream
    readCamera: function () {
        this.socket.send("read_camera");
    },

    // Web controls
    toggleLowLight: function () {
        this.socket.send("toggle_low_light");
    },

    takePhoto: function () {
        this.socket.send("take_photo");
    },

    resDown: function () {
        this.socket.send("res_down");
    },

    resUp: function () {
        this.socket.send("res_up");
    },

    startRecord: function () {
        this.socket.send("start_record");
    },

    stopRecord: function () {
        this.socket.send("stop_record");
    },

    reboot: function () {
        this.socket.send("reboot");
    },

    shutdown: function () {
        this.socket.send("shutdown");
    },

    // Keyboard and controller controls
    tiltCameraUp: function () {
        this.socket.send("camera_up");
    },

    tiltCameraDown: function () {
        this.socket.send("camera_down");
    }
};
