#!/bin/bash

#export DISPLAY
export DISPLAY=:0.0

#Wait for display to initialize
sleep 20

#Call Gnome EOG
/usr/bin/eog -f /home/pi/gro-controller/services/scheduling/start_img.jpg

