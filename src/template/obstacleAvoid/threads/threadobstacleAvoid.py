from src.templates.threadwithstop import ThreadWithStop
from src.utils.messages.allMessages import ObstacleInfo, SteerMotor, Brake, SpeedMotor
from src.utils.messages.messageHandlerSubscriber import messageHandlerSubscriber
from src.utils.messages.messageHandlerSender import messageHandlerSender
from src.statemachine.stateMachine import StateMachine
from src.statemachine.systemMode import SystemMode

class threadobstacleAvoid(ThreadWithStop):
    """This thread handles obstacle avoidance in AUTO mode with real numeric commands."""
    
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

        # Extract obstacle values
        L, C, R = obs.left, obs.center, obs.right

        # Default commands
        steer_cmd = 0   # straight
        brake_cmd = 0   # no braking
        speed_cmd = 100 # forward, safe default within -500..500

        threshold = 5000  # tune this based on your sensor output

        # Obstacle logic
        if C > threshold:
            brake_cmd = 200   # brake moderately
            speed_cmd = 0
        elif L > threshold:
            steer_cmd = 15    # turn right
        elif R > threshold:
            steer_cmd = -15   # turn left

        # Clamp to allowed ranges just in case
        steer_cmd = max(-25, min(25, steer_cmd))
        speed_cmd = max(-500, min(500, speed_cmd))
        brake_cmd = max(-250, min(250, brake_cmd))

        # Send commands
        self.steerSender.send(str(steer_cmd))
        self.brakeSender.send(brake_cmd)
        self.speedSender.send(speed_cmd)

        if self.debugging:
            print(f"[ObstacleAvoid] L:{L} C:{C} R:{R} | Steer:{steer_cmd} Brake:{brake_cmd} Speed:{speed_cmd}")
