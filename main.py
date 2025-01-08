import numpy as np
import time
from car import Car
from util import *
import logging

logging.basicConfig(format='%(asctime)s %(thread)d %(message)s', level=logging.INFO)

import matplotlib
matplotlib.use("Qt5agg")
import matplotlib.pyplot as plt

fig = plt.figure()
mgr = plt.get_current_fig_manager()
print(mgr)
plt.show(block=False)

car = Car()
car.start()

while True:
    dist = car.measure_dist()
    print(dist)
    if dist:
        plt.clf()
        plt.plot(car.dist_history)
        plt_update(mgr)
    time.sleep(0.3)

car.close()
