#!/usr/bin/env bash
set -e

cd "$(dirname "$0")"

echo "Setting up ROS 2 Jazzy..."

if [ ! -f /opt/ros/jazzy/setup.bash ]; then
    echo "Error: ROS 2 Jazzy is not installed."
    exit 1
fi

source /opt/ros/jazzy/setup.bash

if ! command -v colcon >/dev/null 2>&1; then
    echo "Error: colcon is not installed."
    echo "Install it using:"
    echo "sudo apt install python3-colcon-common-extensions"
    exit 1
fi

echo "Building workspace..."

colcon build --symlink-install

source install/setup.bash

echo "Starting Turtlesim Drawing Project..."

ros2 launch turtle_draw draw_launch.py
