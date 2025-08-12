#!/usr/bin/env bash

# Configure environment
export UV_CACHE_DIR=.uv

# Get the number of CPU cores
if [ -f /sys/fs/cgroup/cpu.max ] && ! grep -q "max" /sys/fs/cgroup/cpu.max; then
    read -r max period < /sys/fs/cgroup/cpu.max
    cpu_cores=$((max / period))
else
    cpu_cores=$(nproc)
fi

# Calculate the recommended number of workers
workers=$((cpu_cores * 2 + 1))

# Ensure at least 2 workers are started
if [[ $workers -lt 2 ]]; then
  workers=2
fi

echo "Starting App with ${workers} workers"
uv run fastapi run --workers "$workers" --port 8080 --proxy-headers
