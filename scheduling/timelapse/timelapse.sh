#!/bin/bash
echo "Taking photos for timelapse"
/home/pi/gro-controller/scheduling/timelapse/preppic.py --white
sleep 60
/home/pi/gro-controller/scheduling/timelapse/takepic.sh img_white
sleep 60
/home/pi/gro-controller/scheduling/timelapse/preppic.py --purple
sleep 60
/home/pi/gro-controller/scheduling/timelapse/takepic.sh img_purple on
