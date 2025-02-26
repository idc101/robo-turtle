from car import Car
from util import *
import numpy as np

car = Car()
car.start()

# Colour range for green Duplo blocks
lower = np.array([60, 40, 40], dtype="uint8")
upper = np.array([70, 255, 255], dtype="uint8")

car.rotate_camera_forward()

# Drive around avoiding walls until we see the duplo tower
# Then turn towards it and move forwards
while True:
  if car.check_off_ground():
    break;
  print(car.measure_mpu())

#   cX, cY, area, original = car.find_coloured_shape(lower, upper)
#   cv2.imshow('original', original)
#   cv2.waitKey(1)
#   print(f"x={cX} y={cY}")
#   # 
#   if cX == -1:
#     x = car.measure_dist()
#     print(x)
#     car.forward()
#     if x and x < 30:
#       car.stop()
#       car.rotate_camera_left()
#       l = car.measure_dist()
#       car.rotate_camera_right()
#       r = car.measure_dist()
#       car.rotate_camera_forward()
#       if r > l :
#         car.right(90)
#       else:
#         car.left(90)
#     else:
#       car.forward()
#   elif cX < 380:
#     car.left (5)
#   elif cX > 420:
#     car.right(5)
#   else:
#     car.forward(2)
  


car.close()
