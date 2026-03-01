from setuptools import find_packages, setup

package_name = 'camjam_sensors'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='mike',
    maintainer_email='mikelikesrobots@outlook.com',
    description='Package for CamJam EduKit #3 to publish readings from the sensors',
    license='MIT-0',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'distance = camjam_sensors.hcsr04:main',
            'line = camjam_sensors.line_sensor:main',
        ],
    },
)
