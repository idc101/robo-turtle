import time
import cv2

def plt_update(manager, interval = 0.01):
    if manager is not None:
        canvas = manager.canvas
        if canvas.figure.stale:
            canvas.draw_idle()
        canvas.start_event_loop(interval)
    else:
        time.sleep(interval)

def image_update(car):
    img = car.capture()
    img = cv2.imdecode(img, cv2.IMREAD_UNCHANGED)
    cv2.imshow('Camera', img)
    return img