from car import Car
from util import *

car = Car()
car.start()

car.rotate_camera_forward()



while True:
  if car.check_off_ground():
    break;
  x = car.measure_dist()
  print(x)
  car.forward()
  if x and x < 30:
    car.stop()
    car.rotate_camera_left()
    l = car.measure_dist()
    car.rotate_camera_right()
    r = car.measure_dist()
    car.rotate_camera_forward()
    if r > l :
      car.right(90)
    else:
      car.left(90)
  else:
    car.forward()


car.close()
