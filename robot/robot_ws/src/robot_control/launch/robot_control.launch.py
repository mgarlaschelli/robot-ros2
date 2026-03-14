from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    return LaunchDescription([
        Node(
            package='robot_sensors',
            namespace='robot01',
            executable='distance',
            name='distance',
        ),
        Node(
            package='robot_control',
            namespace='robot01',
            executable='control',
            name='controller',
        ),
        Node(
            package='robot_control',
            namespace='robot01',
            executable='move',
            name='movement',
            parameters=[
                {"max_duty_cycle": 50},
            ]
        ),
        Node(
            package='robot_control',
            namespace='robot01',
            executable='joystick',
            name='joystick',
        ),
    ])
