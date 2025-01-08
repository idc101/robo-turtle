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
    CMD_Ultrasonic_Sensor = 21
    CMD_Car_LeaveTheGround = 23

    def __init__(self):
        self.cmd_no = 0
        self.off = [0.007,  0.022,  0.091,  0.012, -0.011, -0.05]
        self.ip = "192.168.4.1"
        self.port = 100
        self.keep_running = True
        self.commands = queue.Queue()
        self.responses = {}
        self.dist_history = np.array([])

    def connect(self):
        logger.info('Connect to {0}:{1}'.format(self.ip, self.port))
        self.sock = socket.socket()
        try:
            self.sock.connect((self.ip, self.port))
        except:
            logger.info('Error: ', sys.exc_info()[0])
            sys.exit()
        logger.info('Connected!')

    def start(self):
        self.connect()
        self.run_thread = threading.Thread(target=self.run)
        self.run_thread.start()
        self.heartbeat_thread = threading.Thread(target=self.heartbeat, daemon=True)
        self.heartbeat_thread.start()
    
    def close(self):
        self.keep_running = False
        self.run_thread.join()
        self.sock.close()

    def run(self):
        data = ""
        while self.keep_running:
            # Send
            try:
                msg_env = self.commands.get(block=False, timeout=0.005)
                if msg_env['msg'] == '{Heartbeat}': # annoyingly not json
                    json_msg = msg_env['msg']
                else:
                    json_msg = json.dumps(msg_env['msg'])
                logger.info(f"Sending {msg_env['log']} - {json_msg}")
                sent_at = datetime.datetime.now()
                self.sock.send(json_msg.encode())

                # Receive Response - make sure we get a response before sending the next message
                try:
                    while not '}' in data:
                        data = data + self.sock.recv(1024).decode()
                    response = data[0:data.index('}') + 1]
                    data = data[data.index('}') + 1:len(data) - 1]
                    total_delta = datetime.datetime.now() - sent_at
                    log_time = int(total_delta.total_seconds() * 1000)
                    logger.info(f'Received: {response} time={log_time}ms')
                    if msg_env['msg'] != '{Heartbeat}':
                        self.responses[int(msg_env['msg']['H'])] = self.process_response(response)
                except Exception as ex:
                    logger.info(f'Error: {ex}')
                    sys.exit()
            except queue.Empty:
                pass

    def heartbeat(self):
        while self.keep_running:
            self.commands.put({'log': 'heartbeat', 'msg': '{Heartbeat}'})
            time.sleep(0.8)

    def process_response(self, res):
        if res == '{Heartbeat}':
            return 1
        return re.search('_(.*)}', res).group(1)
    
    def send_command(self, description: str, msg: dict):
        self.cmd_no += 1
        msg["H"] = str(self.cmd_no)
        logger.info(f"Queuing: {description} - {msg}")
        self.commands.put({'log': description, 'msg': msg})
        return self.wait_for_response(self.cmd_no)

    def wait_for_response(self, command_no, timeout = 2000):
        start = datetime.datetime.now()
        while command_no not in self.responses:
            time.sleep(0.005)
            time_delta = (datetime.datetime.now() - start)
            time_since_start = time_delta.total_seconds() * 1000 + time_delta.microseconds / 1000
            if time_since_start > timeout:
                logger.info(f"{command_no} timeout {time_since_start}")
                return None
        result = self.responses.pop(command_no, None)
        return result

    def forward(self, distance = 1, speed = 200):
        msg = {"N": self.CMD_CarControl_TimeLimit, "D1": 3, "D2": speed, "T": 500 * distance}
        self.send_command('forward', msg)
        time.sleep((500.0 * distance) / 1000)

    def backward(self, distance = 1, speed = 200):
        msg = {"N": self.CMD_CarControl_TimeLimit, "D1": 4, "D2": speed, "T": 500 * distance}
        self.send_command('backward', msg)
        time.sleep((500.0 * distance) / 1000)

    def left(self, angle = 90, speed = 123):
        # 255 / 250ms also turns 90
        msg = {"N": self.CMD_CarControl_TimeLimit, "D1": 1, "D2": speed, "T": int((500.0 / 90) * angle)}
        self.send_command('left', msg)
        time.sleep((500.0 / 90) * angle / 1000)

    def right(self, angle = 90, speed = 123):
        msg = {"N": self.CMD_CarControl_TimeLimit, "D1": 2, "D2": speed, "T": int((500.0 / 90) * angle)}
        self.send_command('right', msg)
        time.sleep((500.0 / 90) * angle / 1000)

    def stop(self):
        msg = {"N": self.CMD_MotorControl, "D1": 0, "D2": 0, "D3": 1}
        self.send_command('stop', msg)

    def rotate_camera(self, angle = 150):
        msg = {"N": 5, "D1": 1, "D2": angle}
        self.send_command('rotate_camera', msg)

    def measure_dist(self):
        msg = {"N": self.CMD_Ultrasonic_Sensor, "D1": 2}
        dist = self.send_command('measure_dist', msg)
        if dist:
            dist_int = int(dist)
            self.dist_history = np.append(self.dist_history, [dist_int])
            if self.dist_history.size > 6:
                self.dist_history = self.dist_history[-6:]
            return dist_int
        return None

    def check_off_ground(self):
        msg = {"N": self.CMD_Car_LeaveTheGround}
        self.send_command('check_off_ground', msg)

    def capture_image(self):
        cam = urlopen('http://192.168.4.1/capture')
        img = cam.read()
        return np.asarray(bytearray(img), dtype = 'uint8')
