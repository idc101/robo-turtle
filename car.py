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
    def __init__(self):
        self.cmd_no = 0
        self.off = [0.007,  0.022,  0.091,  0.012, -0.011, -0.05]
        self.ip = "192.168.4.1"
        self.port = 100
        self.keep_running = True
        self.commands = queue.Queue()
        self.start_time = datetime.datetime.now()

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
                    #data = data + self.sock.recv(1024).decode()
                    while not '}' in data:
                        data = data + self.sock.recv(1024).decode()
                    response = data[0:data.index('}') + 1]
                    data = data[data.index('}') + 1:len(data) - 1]
                    self.log(f'Response: {response} data: {data}')
                    self.process_response(response)
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

    def forward(self, distance = 1, speed = 150):
        self.cmd_no += 1
        msg = {"H": str(self.cmd_no), "N": 3, "D1": 3, "D2": speed}
        self.commands.put({'log': 'forward', 'msg': msg})
        time.sleep(0.3 * distance)
        self.stop()

    def backward(self, distance = 1, speed = 150):
        self.cmd_no += 1
        msg = {"H": str(self.cmd_no), "N": 3, "D1": 4, "D2": speed}
        self.commands.put({'log': 'backward', 'msg': msg})
        time.sleep(0.3 * distance)
        self.stop()

    def left(self, angle = 90, speed = 150):
        self.cmd_no += 1
        msg = {"H": str(self.cmd_no), "N": 3, "D1": 1, "D2": speed}
        self.commands.put({'log': 'left', 'msg': msg})
        time.sleep((0.35 / 90) * angle)
        self.stop()

    def right(self, angle = 90, speed = 150):
        self.cmd_no += 1
        msg = {"H": str(self.cmd_no), "N": 3, "D1": 2, "D2": speed}
        self.commands.put({'log': 'right', 'msg': msg})
        time.sleep((0.35 / 90) * angle)
        self.stop()

    def stop(self):
        self.cmd_no += 1
        msg = {"H": str(self.cmd_no), "N": 1, "D1": 0, "D2": 0, "D3": 1}
        self.commands.put({'log': 'stop', 'msg': msg})

    def rotate_camera(self, angle = 150):
        self.cmd_no += 1
        msg = {"H": str(self.cmd_no), "N": 5, "D1": 1, "D2": angle}
        self.commands.put({'log': 'rotate_camera', 'msg': msg})

    def measure_dist(self):
        self.cmd_no += 1
        msg = {"H": str(self.cmd_no), "N": 21, "D1": 2}
        self.commands.put({'log': 'measure_dist', 'msg': msg})

    def check_off_ground(self):
        self.cmd_no += 1
        msg = {"H": str(self.cmd_no), "N": 23}
        self.commands.put({'log': 'check_off_ground', 'msg': msg})

    def log(self, msg):
        delta = datetime.datetime.now() - self.start_time
        log_time = int(delta.total_seconds() * 1000)
        print(f"{log_time}: {msg}")
