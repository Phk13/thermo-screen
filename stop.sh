#!/bin/bash
PID_FILE=thermo-screen.pid
PID=$(cat $PID_FILE)
echo "Stopping process with PID $PID "
kill -9 $PID
rm $PID_FILE