from car import Car
from util import *

car = Car()
car.start()

car.rotate_camera_forward()

while not car.check_off_ground():
  x = car.measure_dist()
  print(x)
  if x and x > 20:
    car.forward(1)
  else:
    car.rotate_camera_left()
    l = car.measure_dist()
    car.rotate_camera_right()
    r = car.measure_dist()
    if r > l :
      car.right(90)
    else:
      car.left(90)
    car.rotate_camera_forward()


car.close()
