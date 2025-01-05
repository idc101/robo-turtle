# import numpy as np
# import cv2 as cv
from urllib.request import urlopen
import socket
import sys
import json
import re
# import matplotlib.pyplot as plt
import time
from car import Car

car = Car()
car.start()

car.forward(1)
car.left(90)
car.forward(1)
car.left(90)
car.forward(1)
car.left(90)
car.forward(1)
car.left(90)

car.close()
