# ROS 2 Turtlesim Drawing Project

## Project Overview
This project uses ROS 2 Jazzy and Python to control a simulated turtle and draw geometric shapes and text.

## Author
Mohamed Elsisi

## Environment
- Ubuntu 24.04 LTS
- ROS 2 Jazzy
- Python 3
- Turtlesim

## Project Features
- Circle drawing
- Square drawing
- Triangle drawing
- Half-circle drawing
- Writing the name Mohamed Elsisi
- Pen color control
- Turtle movement using ROS 2 velocity commands
- Pose feedback for accurate movement and rotation

## ROS 2 Topics
- Publisher: /turtle1/cmd_vel
- Subscriber: /turtle1/pose

## ROS 2 Services
- /turtle1/set_pen
- /turtle1/teleport_absolute

## Package Dependencies
- rclpy
- geometry_msgs
- turtlesim
- std_srvs
- launch
- launch_ros

## Installation Requirements

Install the required packages on Ubuntu 24.04 with ROS 2 Jazzy:

sudo apt update
sudo apt install ros-jazzy-turtlesim ros-jazzy-launch-ros python3-colcon-common-extensions

## How to Run

1. Extract the submission ZIP file.
2. Open a terminal inside the extracted folder.
3. Run:

chmod +x run.sh
./run.sh

The script builds the workspace and launches the Turtlesim drawing project.

## Submission Contents
- src/turtle_draw: ROS 2 Python package
- run.sh: Build and launch script
- Project_Demo.webm: Project demonstration video
- Project_Result.png: Final drawing screenshot

