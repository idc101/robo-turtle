import socket
import sys
import json
import re
import time

cmd_no = 0

off = [0.007,  0.022,  0.091,  0.012, -0.011, -0.05]
def cmd(sock, do, what = '', where = '', at = ''):
    global cmd_no
    cmd_no += 1
    msg = {"H":str(cmd_no)} # dictionary
    if do == 'move':
        msg["N"] = 3
        what = ' car '
        if where == 'forward':
            msg["D1"] = 3
        elif where == 'back':
            msg["D1"] = 4
        elif where == 'left':
            msg["D1"] = 1
        elif where == 'right':
            msg["D1"] = 2
        msg["D2"] = at # at is speed here
        where = where + ' '
    elif do == 'stop':
        msg.update({"N":1,"D1":0,"D2":0,"D3":1})
        what = ' car'
    elif do == 'rotate':
        msg.update({"N":5,"D1":1,"D2":at}) # at is an angle here
        what = ' ultrasonic unit'
        where = ' '
    elif do == 'measure':
        if what == 'distance':
            msg.update({"N":21,"D1":2})
        elif what == 'motion':
            msg["N"] = 6
        what = ' ' + what
    elif do == 'check':
        msg["N"] = 23
        what = ' off the ground'
    msg_json = json.dumps(msg)
    print(msg_json)
    print(str(cmd_no) + ': ' + do + what + where + str(at), end = ': ')
    try:
        sock.send(msg_json.encode())
    except:
        print('Error: ', sys.exc_info()[0])
        sys.exit()
    while 1:
        res = sock.recv(1024).decode()
        if '_' in res:
            break
    res = re.search('_(.*)}', res).group(1)
    if res == 'ok' or res == 'true':
        res = 1
    elif res == 'false':
        res = 0
    elif msg.get("N") == 6:
        res = res.split(",")
        res = [int(x)/16384 for x in res] # convert to units of g
        res[2] = res[2] - 1 # subtract 1G from az
        res = [round(res[i] - off[i], 4) for i in range(6)]
    else:
        res = int(res)
    print(res)
    return res

# Connect to car's WiFi
ip = "192.168.4.1"
port = 100
print('Connect to {0}:{1}'.format(ip, port))
car = socket.socket()
try:
    car.connect((ip, port))
except:
    print('Error: ', sys.exc_info()[0])
    sys.exit()
print('Connected!')

# Read first data from socket
print('Receive from {0}:{1}'.format(ip, port))
try:
    data = car.recv(1024).decode()
except:
    print('Error: ', sys.exc_info()[0])
    sys.exit()
print('Received: ', data)

# Main
speed = 150
ang = [90, 10, 170]
dist = [0, 0, 0]
dist_min = 30
cmd(car, do = 'rotate', at = 90)
cmd(car, do = 'move', where = 'forward', at = speed)
time.sleep(1)
while 1:
    start_time = time.time()
    # Check if car was lifted off the ground to interrupt the while loop
    if cmd(car, do = 'check'):
        break
    # Get MPU data and plot it
    mot = cmd(car, do = 'measure', what = 'motion')
    # Check distance to obstacle
    dist[0] = cmd(car, do = 'measure', what = 'distance')
    if dist[0] <= dist_min:
        # Detected an obstacle, stop
        cmd(car, do = 'stop')
        # Rotate ultrasonic unit right and left and measure distance
        found_dir = 0
        for i in range(1,3):
            cmd(car, do = 'rotate', at = ang[i])
            dist[i] = cmd(car, do = 'measure', what = 'distance')
            # Check measured distance
            if dist[i] > dist_min:
                found_dir = 1
        # Rotate ultrasonic unit straight
        cmd(car, do = 'rotate', at = 90)
        # Choose new direction
        if ~found_dir:
            cmd(car, do = 'move', where = 'back', at = speed)
            time.sleep(0.3)
        if dist[1] > dist[2]:
            cmd(car, do = 'move', where = 'right', at = speed)
        else:
            cmd(car, do = 'move', where = 'left', at = speed)
        time.sleep(0.3)
    cmd(car, do = 'move', where = 'forward', at = speed)
    print("--- %s seconds ---" % (time.time() - start_time))

# Close socket
car.close()
