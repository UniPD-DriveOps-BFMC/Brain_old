import cv2
import numpy as np

class SimpleLaneFollower:
    def __init__(self):
        # BFMC tracks usually have white dashed lines and solid lines
        # We tune for white lines on dark asphalt
        self.lower_white = np.array([0, 0, 200])
        self.upper_white = np.array([180, 50, 255])

    def get_steering_angle(self, frame):
        """
        Receives a frame (BGR), returns a steering angle (-25 to +25)
        """
        if frame is None:
            return 0.0

        # 1. Crop to Region of Interest (ROI) - bottom half only
        height, width, _ = frame.shape
        roi = frame[int(height/2):, :]

        # 2. Convert to HSV for better color filtering
        hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)

        # 3. Threshold the image to get only white colors
        self.mask = cv2.inRange(hsv, self.lower_white, self.upper_white)

        # 4. Find the center of the white mass (Centroid)
        # This is a very basic "blob following" logic. 
        # For advanced lanes, use HoughLinesP.
        M = cv2.moments(self.mask)
        
        if M["m00"] != 0:
            cx = int(M["m10"] / M["m00"])
            cy = int(M["m01"] / M["m00"])
            
            # Calculate error from center of the image
            error = cx - (width / 2)
            
            # Simple Proportional Controller (P-Controller)
            # Adjust Kp to tune sensitivity
            Kp = 1.5
            steering_angle = error * Kp
            
            # Clamp values to hardware limits (usually +/- 22 degrees for BFMC cars)
            # steering_angle = max(-22.0, min(22.0, steering_angle))
            
            return float(steering_angle)
        
        return 0.0
    
    def get_image_thresh(self):
        return self.mask