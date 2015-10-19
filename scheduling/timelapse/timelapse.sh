#!/bin/bash
echo "Taking photos for timelapse"
/home/pi/gro-controller/scheduling/timelapse/preppic.py --purple
sleep 40
/home/pi/gro-controller/scheduling/timelapse/takepic.sh img_purple on
sleep 80
/home/pi/gro-controller/scheduling/timelapse/preppic.py --white
sleep 40
/home/pi/gro-controller/scheduling/timelapse/takepic.sh img_white
