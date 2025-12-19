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
        self.obstacleSubscriber = messageHandlerSubscriber(
            self.queuesList, ObstacleInfo, "lastOnly", True
        )

        # Create senders for actuators
        self.steerSender = messageHandlerSender(self.queuesList, SteerMotor)
        self.brakeSender = messageHandlerSender(self.queuesList, Brake)
        self.speedSender = messageHandlerSender(self.queuesList, SpeedMotor)

        # Get state machine instance
        self.stateMachine = StateMachine.get_instance()

        # Default driving parameters
        self.default_speed = 20   # forward speed when clear
        self.brake_value = 0      # 0 = no brake
        self.steer_limit = 21     # max steering angle

        super(threadobstacleAvoid, self).__init__(pause=0.05)  # 50 ms loop

    def thread_work(self):
        """Main loop: reads obstacles and sends commands."""

        # Only act in AUTO mode
        if self.stateMachine.get_mode() != SystemMode.AUTO:
            return

        # Get latest obstacle info
        obs = self.obstacleSubscriber.receive()
        if obs is None:
            # No info → continue at default speed/straight
            self.speedSender.send(self.default_speed)
            self.steerSender.send(0)
            self.brakeSender.send(self.brake_value)
            return

        # Extract obstacle readings
        L, C, R = obs.left, obs.center, obs.right

        # Initialize commands
        steer_cmd = 0
        brake_cmd = 0
        speed_cmd = self.default_speed

        threshold = 5000  # tune based on camera / sensor processing

        # Basic obstacle logic
        if C > threshold:
            brake_cmd = 100          # full brake
            speed_cmd = 0
        elif L > threshold:
            steer_cmd = min(self.steer_limit, 15)   # turn right
        elif R > threshold:
            steer_cmd = max(-self.steer_limit, -15) # turn left

        # Send commands
        self.speedSender.send(speed_cmd)
        self.steerSender.send(steer_cmd)
        self.brakeSender.send(brake_cmd)

        if self.debugging:
            print(
                f"[ObstacleAvoid] L:{L} C:{C} R:{R} | "
                f"Steer:{steer_cmd} Brake:{brake_cmd} Speed:{speed_cmd}"
            )
