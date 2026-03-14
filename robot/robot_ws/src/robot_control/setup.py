from glob import glob
import os
from setuptools import find_packages, setup

package_name = 'robot_control'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'launch'),
            glob(os.path.join('launch', '*launch.[pxy][yma]*'))),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='mg',
    maintainer_email='xgarla@gmail.com',
    description='Package to control the robot',
    license='MIT-0',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'control = robot_control.robot_controller:main',
            'move = robot_control.robot_movement:main',
            'joystick = robot_control.robot_joystick:main',
        ],
    },
)
