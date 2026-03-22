from setuptools import find_packages, setup

package_name = 'robot_sensors'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml'])
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='mg',
    maintainer_email='xgarla@gmail.com',
    description='Package to publish readings from the sensors',
    license='MIT-0',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'distance = robot_sensors.hcsr04:main',
            'camera   = robot_sensors.camera:main',
        ]
    }
)
