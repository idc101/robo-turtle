import pygame
import cv2
import numpy as np
from car import Car

def main():
    # Initialize pygame
    pygame.init()
    
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
    
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_LEFT:
                    car.left()
                if event.key == pygame.K_RIGHT:
                    car.right()
                if event.key == pygame.K_UP:
                    car.forward()
                if event.key == pygame.K_DOWN:
                    car.backward()
            if event.type == pygame.KEYUP:
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