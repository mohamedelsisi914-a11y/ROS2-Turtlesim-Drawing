from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    return LaunchDescription([
        # 1) the turtlesim window
        Node(package="turtlesim", executable="turtlesim_node", output="screen"),
        # 2) our drawing node (it waits for turtlesim's services, so start order is not a problem)
        Node(package="turtle_draw", executable="draw_shapes", output="screen"),
    ])
