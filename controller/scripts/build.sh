#!/bin/bash
set -e

source /opt/ros/jazzy/setup.bash

FRONTEND_DIR=/workspace/controller_ws/src/robot_controller_web/frontend

echo "==> Building frontend..."
cd "$FRONTEND_DIR"
npm install
npm run build

echo "==> Building ROS2 workspace..."
cd /workspace/controller_ws
colcon build --symlink-install --packages-select robot_controller_web

echo ""
echo "Build complete!"
echo "Run 'docker compose up' to start the controller."
