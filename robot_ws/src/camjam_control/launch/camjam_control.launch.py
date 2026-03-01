from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    return LaunchDescription([
        Node(
            package='camjam_sensors',
            namespace='camjam01',
            executable='distance',
            name='distance',
        ),
        Node(
            package='camjam_sensors',
            namespace='camjam01',
            executable='line',
            name='line',
        ),
        Node(
            package='camjam_control',
            namespace='camjam01',
            executable='control',
            name='controller',
        ),
        Node(
            package='camjam_control',
            namespace='camjam01',
            executable='move',
            name='movement',
            parameters=[
                {"max_duty_cycle": 50},
            ]
        ),
    ])
