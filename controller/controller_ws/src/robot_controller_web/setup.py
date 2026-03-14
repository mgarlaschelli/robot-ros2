from setuptools import find_packages, setup

package_name = 'robot_controller_web'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='garla',
    maintainer_email='todo@todo.com',
    description='Web-based robot controller',
    license='MIT-0',
    entry_points={
        'console_scripts': [
            'web = robot_controller_web.main:ros_main',
        ],
    },
)
