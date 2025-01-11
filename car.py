import socket
import sys
import json
import re
import numpy as np
import cv2
from urllib.request import urlopen
import time
import datetime
import threading
import queue
import logging

logger = logging.getLogger(__name__)

class Car:
    CMD_MotorControl = 1
    CMD_CarControl_TimeLimit = 2
    CMD_CarControl_NoTimeLimit = 3
    CMD_Ultrasonic_Sensor = 21
    CMD_Car_LeaveTheGround = 23

    CAMERA_LEFT = 170
    CAMERA_RIGHT = 10
    CAMERA_FORWARD = 90

    def __init__(self):
        self.cmd_no = 0
        self.off = [0.007,  0.022,  0.091,  0.012, -0.011, -0.05]
        self.ip = "192.168.4.1"
        self.port = 100
        self.keep_running = True
        self.commands = queue.Queue()
        self.responses = {}
        self.response_events = {}
        self.dist_history = np.array([])

    def connect(self):
        logger.info('Connect to {0}:{1}'.format(self.ip, self.port))
        self.sock = socket.socket()
        try:
            self.sock.connect((self.ip, self.port))
        except:
            logger.info('connect error: ', sys.exc_info()[0])
            sys.exit()
        logger.info('Connected!')

    def start(self):
        self.connect()
        self.run_thread = threading.Thread(target=self.run)
        self.run_thread.start()
    
    def close(self):
        self.keep_running = False
        self.run_thread.join()
        self.sock.close()

    def run(self):
        data = ""
        sent_at = None
        while self.keep_running:
            # Receive (we will get sent a heartbeat initially)
            try:
                while not '}' in data:
                    data = data + self.sock.recv(1024).decode()
                response = data[0:data.index('}') + 1]
                data = data[data.index('}') + 1:len(data) - 1]
                if response == '{Heartbeat}':
                    self.sock.send('{Heartbeat}'.encode())
                else:
                    total_delta = datetime.datetime.now() - sent_at
                    log_time = int(total_delta.total_seconds() * 1000)
                    logger.info(f'Received: {response} time={log_time}ms')
                    self.responses[int(msg_env['msg']['H'])] = self.process_response(response)
                    event = self.response_events.get(int(msg_env['msg']['H']), None)
                    if event:
                        event.set()
            except Exception as ex:
                logger.info(f'run error', exc_info=ex)
                sys.exit()

            # Send
            try:
                msg_env = self.commands.get(block=False, timeout=0.005)
                json_msg = json.dumps(msg_env['msg'])
                logger.info(f"Sending {msg_env['log']} - {json_msg}")
                sent_at = datetime.datetime.now()
                self.sock.send(json_msg.encode())
            except queue.Empty:
                pass

    def process_response(self, res):
        if res == '{Heartbeat}':
            return 1
        return re.search('_(.*)}', res).group(1)
    
    def send_command(self, description: str, msg: dict, wait_time: float = 0.5):
        self.cmd_no += 1
        this_cmd_no = self.cmd_no
        msg["H"] = str(this_cmd_no)
        logger.info(f"Queuing: {description} - {msg}")
        event = threading.Event()
        self.response_events[this_cmd_no] = event
        self.commands.put({'log': description, 'msg': msg})

        # Wait for response
        result = None
        if event.wait(wait_time):
            result = self.responses.pop(this_cmd_no, None)
        else:
            logger.warning(f"timeout waiting for command {this_cmd_no}")
        self.response_events.pop(this_cmd_no)
        return result

    def forward(self, distance = None, speed = 100):
        if distance:
            msg = {"N": self.CMD_CarControl_TimeLimit, "D1": 3, "D2": speed, "T": 500 * distance}
            self.send_command('forward', msg, (500.0 * distance) / 1000)
        else:
            msg = {"N": self.CMD_CarControl_NoTimeLimit, "D1": 3, "D2": speed}
            self.send_command('forward', msg)

    def backward(self, distance = None, speed = 100):
        if distance:
            msg = {"N": self.CMD_CarControl_TimeLimit, "D1": 4, "D2": speed, "T": 500 * distance}
            self.send_command('backward', msg, (500.0 * distance) / 1000)
        else:
            msg = {"N": self.CMD_CarControl_NoTimeLimit, "D1": 4, "D2": speed}
            self.send_command('backward', msg)

    def left(self, angle = 90, speed = 123):
        # 255 / 250ms also turns 90
        msg = {"N": self.CMD_CarControl_TimeLimit, "D1": 1, "D2": speed, "T": int((500.0 / 90) * angle)}
        self.send_command('left', msg, (500.0 / 90) * angle / 1000)

    def right(self, angle = 90, speed = 123):
        msg = {"N": self.CMD_CarControl_TimeLimit, "D1": 2, "D2": speed, "T": int((500.0 / 90) * angle)}
        self.send_command('right', msg, (500.0 / 90) * angle / 1000)

    def stop(self):
        msg = {"N": self.CMD_MotorControl, "D1": 0, "D2": 0, "D3": 1}
        self.send_command('stop', msg)

    def rotate_camera_left(self):
        self.rotate_camera(self.CAMERA_LEFT)

    def rotate_camera_right(self):
        self.rotate_camera(self.CAMERA_RIGHT)

    def rotate_camera_forward(self):
        self.rotate_camera(self.CAMERA_FORWARD)

    def rotate_camera(self, angle = 150):
        msg = {"N": 5, "D1": 1, "D2": angle}
        self.send_command('rotate_camera', msg)

    def measure_dist(self) -> int:
        msg = {"N": self.CMD_Ultrasonic_Sensor, "D1": 2}
        dist = self.send_command('measure_dist', msg, 2.0)
        if dist:
            dist_int = int(dist)
            self.dist_history = np.append(self.dist_history, [dist_int])
            if self.dist_history.size > 6:
                self.dist_history = self.dist_history[-6:]
            return dist_int
        return None

    def check_off_ground(self):
        msg = {"N": self.CMD_Car_LeaveTheGround}
        res = self.send_command('check_off_ground', msg, 2.0)
        return res == "true"

    def capture_image(self):
        cam = urlopen('http://192.168.4.1/capture')
        img = cam.read()
        return np.asarray(bytearray(img), dtype = 'uint8')
