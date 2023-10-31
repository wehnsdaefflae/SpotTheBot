#!/bin/bash

redis-server databases/general.conf &

# Wait for a moment to ensure the first instance starts without issues
sleep 2

redis-server databases/markers.conf &

echo "Both Redis instances have been started."