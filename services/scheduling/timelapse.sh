#bin/bash
n=$[5+1]
next_n=$[$n+1]
sed -i "2s/.*/n=$next_n/" ${0}
echo $n

fswebcam -r 1080x720 --no-banner /home/pi/images/image$n.jpg
# convert images/*.jpg images/a.gif
