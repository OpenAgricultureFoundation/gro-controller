#!/usr/bin/env bash

# Add to cron to run every min...
# ...crontab -e
# ...* * * * * /home/pi/gro-controller/services/scheduling/sched_grodaemon_cron.sh

PIDFILE="$HOME/tmp/grodaemon.pid"

if [ -e "${PIDFILE}" ] && (ps -p $(cat ${PIDFILE}) > /dev/null); then
  echo "Already running."
  exit 99
fi

/home/pi/gro-controller/grodaemon.py
