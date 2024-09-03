#!/bin/bash
PID_FILE=thermo-screen.pid
if [ -f "$PID_FILE" ]; then
    PID=$(cat $PID_FILE)
    if ps -p $PID > /dev/null
    then
        echo "Process is already running with PID $PID"
        exit
    fi
fi
nohup python3 main.py > debug.log 2>&1 & 
echo $! > $PID_FILE
echo "Started with PID $!"