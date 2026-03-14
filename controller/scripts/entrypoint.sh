#!/bin/bash
set -e

source /opt/ros/jazzy/setup.bash

# Source the built workspace if it exists
if [ -f /workspace/controller_ws/install/setup.bash ]; then
    source /workspace/controller_ws/install/setup.bash
fi

exec "$@"
