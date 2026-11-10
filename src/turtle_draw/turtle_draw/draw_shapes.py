#!/usr/bin/env python3
"""draw_shapes.py - draws shapes (and later a name) in turtlesim using cmd_vel + services."""
import math
import time

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from std_srvs.srv import Empty
from turtlesim.msg import Pose
from turtlesim.srv import SetPen, TeleportAbsolute

RATE_HZ = 50.0  # how many cmd_vel messages per second while moving

# ---------- letters: each letter = list of polylines, points are (x, y) in letter units ----------
# letter height = 1.0 (capital / tall letters), small letters are 0.6 high
OCTAGON = [(0.1, 0), (0.4, 0), (0.5, 0.1), (0.5, 0.5), (0.4, 0.6), (0.1, 0.6), (0, 0.5), (0, 0.1), (0.1, 0)]
GLYPHS = {
    "M": (0.8, [[(0, 0), (0, 1), (0.4, 0.4), (0.8, 1), (0.8, 0)]]),
    "o": (0.5, [OCTAGON]),
    "h": (0.5, [[(0, 0), (0, 1)], [(0, 0.5), (0.1, 0.6), (0.4, 0.6), (0.5, 0.5), (0.5, 0)]]),
    "a": (0.5, [OCTAGON, [(0.5, 0.6), (0.5, 0)]]),
    "m": (0.8, [[(0, 0), (0, 0.6)],
                [(0, 0.5), (0.1, 0.6), (0.3, 0.6), (0.4, 0.5), (0.4, 0)],
                [(0.4, 0.5), (0.5, 0.6), (0.7, 0.6), (0.8, 0.5), (0.8, 0)]]),
    "e": (0.5, [[(0, 0.3), (0.5, 0.3), (0.5, 0.5), (0.4, 0.6), (0.1, 0.6), (0, 0.5),
                 (0, 0.1), (0.1, 0), (0.4, 0), (0.5, 0.1)]]),
    "d": (0.5, [OCTAGON, [(0.5, 0), (0.5, 1)]]),
    "E": (0.5, [[(0.5, 1), (0, 1), (0, 0), (0.5, 0)], [(0, 0.5), (0.4, 0.5)]]),
    "l": (0.0, [[(0, 0), (0, 1)]]),
    "s": (0.5, [[(0.5, 0.6), (0, 0.6), (0, 0.3), (0.5, 0.3), (0.5, 0), (0, 0)]]),
    "i": (0.0, [[(0, 0), (0, 0.6)], [(0, 0.82), (0, 0.95)]]),
    " ": (0.6, []),
}
LETTER_GAP = 0.3  # space between letters (letter units)


def wrap_angle(a):
    """Wrap an angle to the range [-pi, pi]."""
    return math.atan2(math.sin(a), math.cos(a))


class TurtleDrawer(Node):
    def __init__(self):
        super().__init__("turtle_drawer")
        self.cmd_pub = self.create_publisher(Twist, "/turtle1/cmd_vel", 10)
        self.pen_client = self.create_client(SetPen, "/turtle1/set_pen")
        self.tp_client = self.create_client(TeleportAbsolute, "/turtle1/teleport_absolute")
        self.clear_client = self.create_client(Empty, "/clear")
        self.pen_style = (255, 255, 255, 3)  # last pen colour/width (r, g, b, width)
        self.pose = None  # latest turtle pose (filled by the subscriber below)
        self.pose_count = 0  # how many pose messages we received so far
        self.create_subscription(Pose, "/turtle1/pose", self._pose_cb, 1)
        for client in (self.pen_client, self.tp_client, self.clear_client):
            while not client.wait_for_service(timeout_sec=1.0):
                self.get_logger().warn("Waiting for turtlesim... (is turtlesim_node running?)")
        while self.pose is None:  # wait for the first pose message
            rclpy.spin_once(self, timeout_sec=0.1)
        self.get_logger().info("Turtle drawer ready")

    def _pose_cb(self, msg):
        self.pose = msg
        self.pose_count += 1

    def _fresh_pose(self):
        """Wait for a NEW pose message, so we never use an old position/angle."""
        count = self.pose_count
        deadline = time.monotonic() + 1.0
        while self.pose_count == count and time.monotonic() < deadline:
            rclpy.spin_once(self, timeout_sec=0.05)

    # ---------- low level ----------
    def _publish_for(self, linear, angular, duration):
        """Publish one Twist repeatedly for `duration` seconds, then stop."""
        msg = Twist()
        msg.linear.x = float(linear)
        msg.angular.z = float(angular)
        end = time.monotonic() + duration
        while time.monotonic() < end:
            self.cmd_pub.publish(msg)
            time.sleep(1.0 / RATE_HZ)
        self.cmd_pub.publish(Twist())  # all zeros = stop
        time.sleep(0.1)

    # ---------- services ----------
    def set_pen(self, r=255, g=255, b=255, width=3, off=False):
        if not off:
            self.pen_style = (r, g, b, width)
        req = SetPen.Request()
        req.r, req.g, req.b = int(r), int(g), int(b)
        req.width = int(width)
        req.off = 1 if off else 0
        future = self.pen_client.call_async(req)
        rclpy.spin_until_future_complete(self, future)

    def teleport(self, x, y, theta_deg=0.0):
        req = TeleportAbsolute.Request()
        req.x, req.y = float(x), float(y)
        req.theta = math.radians(theta_deg)
        future = self.tp_client.call_async(req)
        rclpy.spin_until_future_complete(self, future)

    def jump_to(self, x, y, theta_deg=0.0):
        """Move without drawing: pen up -> teleport -> pen down (same colour)."""
        r, g, b, w = self.pen_style
        self.set_pen(r, g, b, w, off=True)
        self.teleport(x, y, theta_deg)
        time.sleep(0.08)  # let turtlesim apply the teleport while the pen is still up
        self.set_pen(r, g, b, w, off=False)

    def clear_screen(self):
        future = self.clear_client.call_async(Empty.Request())
        rclpy.spin_until_future_complete(self, future)

    # ---------- motions ----------
    def move_forward(self, distance, speed=2.0):
        """time = distance / speed"""
        self._publish_for(speed, 0.0, abs(distance) / speed)

    def move_precise(self, distance, speed=2.0):
        """Drive `distance` using the pose feedback: stop when the travelled distance is reached."""
        self._fresh_pose()
        x0, y0 = self.pose.x, self.pose.y
        deadline = time.monotonic() + abs(distance) / speed + 3.0  # safety timeout
        while time.monotonic() < deadline:
            rclpy.spin_once(self, timeout_sec=0.02)  # wait for a fresh pose
            remaining = distance - math.hypot(self.pose.x - x0, self.pose.y - y0)
            if remaining <= 0.01:
                break
            msg = Twist()
            msg.linear.x = min(speed, max(0.3, 3.0 * remaining))  # slow down near the target
            self.cmd_pub.publish(msg)
        self.cmd_pub.publish(Twist())  # stop
        time.sleep(0.1)

    def rotate(self, angle_deg, speed_deg=90.0, absolute=False):
        """Turn using the pose feedback (positive = counter-clockwise).
        absolute=False: turn BY angle_deg.  absolute=True: turn TO the heading angle_deg.
        error = target - current angle ; w = K * error (limited to the max speed)."""
        self._fresh_pose()
        if absolute:
            target = wrap_angle(math.radians(angle_deg))
        else:
            target = wrap_angle(self.pose.theta + math.radians(angle_deg))
        max_w = math.radians(speed_deg)
        deadline = time.monotonic() + 5.0  # safety timeout
        while time.monotonic() < deadline:
            rclpy.spin_once(self, timeout_sec=0.02)  # wait for a fresh pose
            error = wrap_angle(target - self.pose.theta)
            if abs(error) < math.radians(0.3):
                break
            w = math.copysign(min(max_w, max(0.15, 3.0 * abs(error))), error)
            msg = Twist()
            msg.angular.z = w
            self.cmd_pub.publish(msg)
        self.cmd_pub.publish(Twist())  # stop
        time.sleep(0.1)

    def arc(self, radius, angle_deg, speed=1.5):
        """Drive on a circle: w = v / r, time = angle / w (counter-clockwise)."""
        w = speed / radius
        self._publish_for(speed, w, math.radians(angle_deg) / w)

    # ---------- shapes ----------
    def draw_circle(self, cx, cy, r=1.2, color=(255, 80, 80)):
        """Full circle: start at the bottom point heading east, drive 360 degrees."""
        self.jump_to(cx, cy - r, 0.0)
        self.set_pen(*color)
        self.arc(r, 360.0)

    def draw_square(self, x, y, side=2.4, color=(80, 255, 80)):
        """4 sides, turn 360/4 = 90 degrees after each side."""
        self.jump_to(x, y, 0.0)
        self.set_pen(*color)
        for _ in range(4):
            self.move_precise(side)
            self.rotate(90.0)

    def draw_triangle(self, x, y, side=2.6, color=(255, 255, 80)):
        """Equilateral triangle: 3 sides, turn 360/3 = 120 degrees after each side."""
        self.jump_to(x, y, 0.0)
        self.set_pen(*color)
        for _ in range(3):
            self.move_precise(side)
            self.rotate(120.0)

    def draw_half_circle(self, cx, cy, r=1.3, color=(80, 200, 255)):
        """Half circle: arc of 180 degrees, then close it with the diameter (2 * r)."""
        self.jump_to(cx + r, cy, 90.0)
        self.set_pen(*color)
        self.arc(r, 180.0)
        self.rotate(0.0, absolute=True)  # face east: the diameter is a horizontal line
        self.move_precise(2 * r)

    # ---------- text ----------
    def draw_line(self, x1, y1, x2, y2, speed=1.5):
        """Straight line between two points: jump to start, face the end, drive the distance."""
        dx, dy = x2 - x1, y2 - y1
        distance = math.hypot(dx, dy)
        if distance < 1e-6:
            return
        heading = math.degrees(math.atan2(dy, dx))  # angle of the line
        self.jump_to(x1, y1, heading)
        self.move_forward(distance, speed)

    def draw_text(self, text, cx=5.5, cy=5.5, scale=0.85, color=(255, 255, 255)):
        """Write `text` centred at (cx, cy). Every stroke is a straight line (see GLYPHS)."""
        total = sum(GLYPHS[c][0] for c in text) + LETTER_GAP * (len(text) - 1)
        x = cx - total * scale / 2.0       # left edge so the text is centred
        y = cy - 0.5 * scale               # bottom edge (letter height = 1.0 * scale)
        self.set_pen(*color)
        for ch in text:
            width, strokes = GLYPHS[ch]
            for stroke in strokes:
                for (ax, ay), (bx, by) in zip(stroke, stroke[1:]):
                    self.draw_line(x + ax * scale, y + ay * scale,
                                   x + bx * scale, y + by * scale)
            x += (width + LETTER_GAP) * scale


def main(args=None):
    rclpy.init(args=args)
    drawer = TurtleDrawer()
    try:
        drawer.clear_screen()
        drawer.draw_circle(2.5, 8.5)
        drawer.draw_square(7.0, 7.3)
        drawer.draw_triangle(1.3, 2.0)
        drawer.draw_half_circle(8.2, 2.5)
        drawer.draw_text("Mohamed Elsisi")
        drawer.jump_to(5.5, 0.8, 90.0)  # park the turtle below the drawing
        drawer.get_logger().info("Drawing done")
    except KeyboardInterrupt:
        pass
    drawer.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()
