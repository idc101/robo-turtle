import numpy as np
import time
from car import Car
from util import *


car = Car()
car.start()

CAMERA_LEFT = 170
CAMERA_RIGHT = 10
CAMERA_FORWARD = 90

car.rotate_camera(CAMERA_FORWARD)

while not car.check_off_ground():
  x = car.measure_dist()
  print(x)
  if x and x > 30:
    car.forward(1)
  else:
    car.rotate_camera(CAMERA_LEFT)
    l = car.measure_dist()
    car.rotate_camera(CAMERA_RIGHT)
    r = car.measure_dist()
    if r > l :
      car.right(90)
    else:
      car.left(90)
    car.rotate_camera(CAMERA_FORWARD)


car.close()
