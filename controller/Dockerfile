FROM ros:jazzy

# System deps + Node.js 20
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3-pip \
    python3-colcon-common-extensions \
    ros-jazzy-std-srvs \
    ros-jazzy-geometry-msgs \
    curl \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

# Python deps (system-wide so rclpy and FastAPI share the same interpreter)
RUN pip3 install --break-system-packages fastapi "uvicorn[standard]"

WORKDIR /workspace

COPY scripts/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
CMD ["uvicorn", "robot_controller_web.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload", "--reload-dir", "/workspace/controller_ws/src/robot_controller_web/robot_controller_web"]
