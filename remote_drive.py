import pygame
import cv2
import numpy as np
from car import Car

DIRECTION_STOP = 0
DIRECTION_LEFT = 1
DIRECTION_RIGHT = 2
DIRECTION_FORWARD = 4
DIRECTION_BACK = 8
DIRECTION_LEFT_FORWARD = DIRECTION_LEFT + DIRECTION_FORWARD
DIRECTION_RIGHT_FORWARD = DIRECTION_RIGHT + DIRECTION_FORWARD
DIRECTION_LEFT_BACK = DIRECTION_LEFT + DIRECTION_BACK
DIRECTION_RIGHT_BACK = DIRECTION_RIGHT + DIRECTION_BACK

def main():
    # Initialize pygame
    pygame.init()
    
    clock = pygame.time.Clock()

    # Connect to the car
    car = Car()
    car.start()

    # Set up webcam
    cap = cv2.VideoCapture('http://192.168.4.1/Test')
    if not cap.isOpened():
        print("Error: Could not open webcam.")
        return
    
    # Get webcam properties
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    
    # Set up pygame window
    screen = pygame.display.set_mode((width, height))
    pygame.display.set_caption("Webcam Stream")
    
    direction = DIRECTION_STOP

    running = True
    while running:
        clock.tick(30)

        current_direction = direction
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_LEFT:
                    direction = direction | DIRECTION_LEFT
                if event.key == pygame.K_RIGHT:
                    direction = direction | DIRECTION_RIGHT
                if event.key == pygame.K_UP:
                    direction = direction | DIRECTION_FORWARD
                if event.key == pygame.K_DOWN:
                    direction = direction | DIRECTION_BACK
            if event.type == pygame.KEYUP:
                if event.key == pygame.K_LEFT:
                    direction = direction ^ DIRECTION_LEFT
                if event.key == pygame.K_RIGHT:
                    direction = direction ^ DIRECTION_RIGHT
                if event.key == pygame.K_UP:
                    direction = direction ^ DIRECTION_FORWARD
                if event.key == pygame.K_DOWN:
                    direction = direction ^ DIRECTION_BACK
        if current_direction != direction:
            if direction == DIRECTION_LEFT:
                car.left()
            elif direction == DIRECTION_RIGHT:
                car.right()
            elif direction == DIRECTION_FORWARD:
                car.forward()
            elif direction == DIRECTION_BACK:
                car.backward()
            elif direction == DIRECTION_LEFT_FORWARD:
                car.left_forward()
            elif direction == DIRECTION_RIGHT_FORWARD:
                car.right_forward()
            elif direction == DIRECTION_LEFT_BACK:  
                car.left_backward()
            elif direction == DIRECTION_RIGHT_BACK:
                car.right_backward()
            else:
                car.stop()

        # Capture frame-by-frame
        ret, frame = cap.read()
        if not ret:
            print("Error: Could not read frame.")
            break
        
        # Convert frame from BGR to RGB (pygame uses RGB, OpenCV uses BGR)
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Convert frame to a format pygame can display
        frame = np.rot90(frame)  # Rotate because pygame's default is different
        frame = pygame.surfarray.make_surface(frame)
        
        # Display frame
        screen.blit(frame, (0, 0))
        pygame.display.flip()
    
    # Release resources
    cap.release()
    car.close()
    pygame.quit()

if __name__ == "__main__":
    main()