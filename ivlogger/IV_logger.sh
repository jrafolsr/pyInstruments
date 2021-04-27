#!/bin/bash
echo "Launching program"
python3 /home/pi/Documents/PythonScripts/pyInstruments/ivlogger/IV_GUI.py &
echo "Launching chromium"
sleep 3s
chromium-browser --URL http://127.0.0.1:8053 --remote-debugging-port=9222 &
$SHELL