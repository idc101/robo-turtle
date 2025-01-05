import socket
import socket
import sys
import json
import re
# import matplotlib.pyplot as plt
import time
import datetime
import threading
import queue

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
        self.start_time = datetime.datetime.now()
        self.last_time = self.start_time

    def connect(self):
        self.log('Connect to {0}:{1}'.format(self.ip, self.port))
        self.sock = socket.socket()
        try:
            self.sock.connect((self.ip, self.port))
        except:
            self.log('Error: ', sys.exc_info()[0])
            sys.exit()
        self.log('Connected!')

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
                    self.log(f"{msg_env['log']} - {json_msg}")
                self.sock.send(json_msg.encode())

                # Receive Response - make sure we get a response before sending the next message
                try:
                    while not '}' in data:
                        data = data + self.sock.recv(1024).decode()
                    response = data[0:data.index('}') + 1]
                    data = data[data.index('}') + 1:len(data) - 1]
                    if msg_env['msg'] != '{Heartbeat}':
                        self.log(f'Response: {response}')
                        self.responses[int(msg_env['msg']['H'])] = self.process_response(response)
                except Exception as ex:
                    self.log(f'Error: {ex}')
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
        res = re.search('_(.*)}', res).group(1)
        if res == 'ok' or res == 'true':
            res = 1
        elif res == 'false':
            res = 0
        # elif msg.get("N") == 6:
        #     res = res.split(",")
        #     res = [int(x)/16384 for x in res] # convert to units of g
        #     res[2] = res[2] - 1 # subtract 1G from az
        #     res = [round(res[i] - self.off[i], 4) for i in range(6)]
        else:
            res = int(res)
        return res
    
    def send_command(self, description: str, msg: dict):
        self.cmd_no += 1
        msg["H"] = str(self.cmd_no)
        self.commands.put({'log': description, 'msg': msg})
        self.wait_for_response(self.cmd_no)

    def wait_for_response(self, command_no, timeout = 0.5):
        start = datetime.datetime.now()
        while command_no not in self.responses:
            time.sleep(0.005)
            if (datetime.datetime.now() - start).total_seconds() > timeout:
                break

    def forward(self, distance = 1, speed = 200):
        msg = {"N": self.CMD_CarControl_TimeLimit, "D1": 3, "D2": speed, "T": 500}
        self.send_command('forward', msg)

    def backward(self, distance = 1, speed = 200):
        msg = {"N": self.CMD_CarControl_TimeLimit, "D1": 4, "D2": speed, "T": 500}
        self.send_command('backward', msg)

    def left(self, angle = 90, speed = 123):
        # 255 / 250ms also turns 90
        msg = {"N": self.CMD_CarControl_TimeLimit, "D1": 1, "D2": speed, "T": int((500.0 / 90) * angle)}
        self.send_command('left', msg)

    def right(self, angle = 90, speed = 123):
        msg = {"N": self.CMD_CarControl_TimeLimit, "D1": 2, "D2": speed, "T": int((500.0 / 90) * angle)}
        self.send_command('right', msg)

    def stop(self):
        msg = {"N": self.CMD_MotorControl, "D1": 0, "D2": 0, "D3": 1}
        self.send_command('stop', msg)

    def rotate_camera(self, angle = 150):
        msg = {"N": 5, "D1": 1, "D2": angle}
        self.send_command('rotate_camera', msg)

    def measure_dist(self):
        msg = {"N": self.CMD_Ultrasonic_Sensor, "D1": 2}
        self.send_command('measure_dist', msg)

    def check_off_ground(self):
        msg = {"N": self.CMD_Car_LeaveTheGround}
        self.send_command('check_off_ground', msg)

    def log(self, msg):
        now = datetime.datetime.now()
        total_delta = now - self.start_time
        delta = now - self.last_time
        log_time = int(total_delta.total_seconds() * 1000)
        delta_time = int(delta.total_seconds() * 1000)
        self.last_time = now
        print(f"{log_time} ({delta_time}): {msg}")
