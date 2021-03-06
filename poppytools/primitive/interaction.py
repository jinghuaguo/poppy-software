import time
import numpy

from collections import deque

import pypot.primitive


class SmartCompliance(pypot.primitive.LoopPrimitive):
    def __init__(self, poppy_robot, motor_list, freq=50, ):
        pypot.primitive.LoopPrimitive.__init__(self,poppy_robot, freq)

        self.poppy_robot = poppy_robot
        self.motor_list = [self.get_mockup_motor(m) for m in motor_list]

        self.compute_angle_limit()

    def update(self):
        for i, m in enumerate(self.motor_list):
            angle_limit = self.angles[i]
            if (min(angle_limit) > m.present_position) or (m.present_position > max(angle_limit)):
                m.compliant = False
            else:
                m.compliant = True

    def compute_angle_limit(self):
        self.angles = []
        for m in self.motor_list:
            ang = numpy.asarray(m.angle_limit) if m.direct else -1 * numpy.asarray(m.angle_limit)
            ang = ang - m.offset
            self.angles.append(ang)


class ArmsCompliant(pypot.primitive.LoopPrimitive):
    def start(self):
        for m in self.robot.arms:
            m.compliant = True
        pypot.primitive.LoopPrimitive.start(self)

    def update(self):
        pass


class ArmsCopyMotion(pypot.primitive.LoopPrimitive):
    def start(self):
        for m in self.robot.arms:
            m.moving_speed =  0

        for m in self.robot.l_arm:
            m.compliant = True
        for m in self.robot.r_arm:
            m.compliant = False

        pypot.primitive.LoopPrimitive.start(self)

    def update(self):
        for lm, rm in zip(self.robot.l_arm, self.robot.r_arm):
            rm.goal_position = lm.present_position * (1 if lm.direct else -1)

    def teardown(self):
        for m in self.robot.arms:
            m.compliant = False
            m.goto_position(0,2)

        time.sleep(2)
        for m in self.robot.arms:
            m.moving_speed = 0






class ArmsTurnCompliant(pypot.primitive.LoopPrimitive):
    def __init__(self, poppy_robot, freq):
        pypot.primitive.LoopPrimitive.__init__(self, poppy_robot, freq)

        self.poppy_robot = poppy_robot

        for m in self.poppy_robot.arms:
            m.compliant = False

        for m in self.poppy_robot.arms:
            m.torque_limit = 20

        self.left_arm_torque = deque([0], 0.2 * freq)
        self.right_arm_torque = deque([0], 0.2 * freq)

    def update(self):
        self.left_arm_torque.append(numpy.max([abs(m.present_load) for m in self.poppy_robot.l_arm]))
        self.right_arm_torque.append(numpy.max([abs(m.present_load) for m in self.poppy_robot.r_arm]))

        if numpy.mean(self.left_arm_torque) > 20:
            for m in self.poppy_robot.l_arm:
                m.compliant = True

        elif numpy.mean(self.left_arm_torque) < 7:
            for m in self.poppy_robot.l_arm:
                m.compliant = False

        if numpy.mean(self.right_arm_torque) > 20:
            for m in self.poppy_robot.r_arm:
                m.compliant = True

        elif numpy.mean(self.right_arm_torque) < 7:
            for m in self.poppy_robot.r_arm:
                m.compliant = False
