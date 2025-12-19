from src.templates.threadwithstop import ThreadWithStop
from src.utils.messages.allMessages import ObstacleInfo, SteerMotor, Brake, SpeedMotor
from src.utils.messages.messageHandlerSubscriber import messageHandlerSubscriber
from src.utils.messages.messageHandlerSender import messageHandlerSender
from src.statemachine.stateMachine import StateMachine
from src.statemachine.systemMode import SystemMode
import time

class threadobstacleAvoid(ThreadWithStop):
    """This thread handles obstacle avoidance in AUTO mode."""
    
    def __init__(self, queuesList, logger, debugging=False):
        self.queuesList = queuesList
        self.logger = logger
        self.debugging = debugging
        
        # Subscribe to obstacles
        self.obstacleSubscriber = messageHandlerSubscriber(self.queuesList, ObstacleInfo, "lastOnly", True)
        
        # Create senders for actuators
        self.steerSender = messageHandlerSender(self.queuesList, SteerMotor)
        self.brakeSender = messageHandlerSender(self.queuesList, Brake)
        self.speedSender = messageHandlerSender(self.queuesList, SpeedMotor)
        
        # Get state machine instance
        self.stateMachine = StateMachine.get_instance()
        
        super(threadobstacleAvoid, self).__init__(pause=0.05)  # 50 ms loop

    def thread_work(self):
        """Main loop: reads obstacles and sends commands."""
        # Only act in AUTO mode
        if self.stateMachine.get_mode() != SystemMode.AUTO:
            return
        
        # Get latest obstacle info
        obs = self.obstacleSubscriber.receive()
        if obs is None:
            return

        # Basic obstacle logic:
        # - If center obstacle detected, slow down or brake
        # - Steer away from side obstacles if center is blocked
        L, C, R = obs.left, obs.center, obs.right

        steer_cmd = 0   # 0 = straight
        brake_cmd = "release"
        speed_cmd = "forward"

        threshold = 5000  # tune this based on your Canny sum values

        if C > threshold:
            brake_cmd = "brake"
            speed_cmd = "stop"
        elif L > threshold:
            steer_cmd = 15   # turn right
        elif R > threshold:
            steer_cmd = -15  # turn left

        # Send commands
        self.steerSender.send(str(steer_cmd))
        self.brakeSender.send(brake_cmd)
        self.speedSender.send(speed_cmd)

        if self.debugging:
            print(f"[ObstacleAvoid] L:{L} C:{C} R:{R} | Steer:{steer_cmd} Brake:{brake_cmd} Speed:{speed_cmd}")
