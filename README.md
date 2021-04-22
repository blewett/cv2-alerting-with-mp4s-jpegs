# cv2-alerting-with-mp4s-jpegs
![alt text](https://github.com/blewett/cv2-alerting-with-mp4s-jpegs/blob/main/images/street2.jpeg?raw=true)

This system is built on the Open Computer Vision module – usually referred to as cv2. Install it, after installing python, with the
following:

pip install opencv-python

cv2 is the bit that contains all of the magic.

![alt text](https://github.com/blewett/cv2-alerting-with-mp4s-jpegs/blob/main/images/street.jpeg?raw=true)

There is a wide interest in using video cameras for monitoring.  There are many commercial systems on the market that do this.  Most of those systems have a monthly subscription fee.  The fees cover Internet storage of videos and images (usually jpeg or mp4 format) and some form of alerting system.  The alerting systems send text messages or an emails when motion occurs in front the one or more cameras and have a system for group storage of images from multiple cameras.  The system contained here does all of this and requires no subscription fees.  Further, this system is under the control of the user, rather than a commercial entity.  Monitoring can be setup on most any computer with an attached video camera.

Recording starts when motion is detected.  Recording stops when motion ends.  There are options for scaling and tweaking the detection.  There are options for group storage on a machine of your choice and the storage machine can be local or one of your choosing on the Internet.  Email and text may be sent via gmail – thank you google.

The following is a sample invocation of the system:

python3 camera_monitor.py -write-jpgs

This will result in jpeg images being written to the current directory when motion occurs in front of the camera.  The default is to create mp4 videos and the -write-jpgs option overrides that.  There are many options that the user can set to change the behavior of the system.  The system provided defaults for options work for most people and need not be set to use the system.  Of course, the user has the python code and can modify it as they wish.

The repository contains python files for capturing motion events and php code for uploading those captured images.  There is a doc file that explains how to setup and use the system across platforms.

Doug Blewett

doug.blewett@gmail.com
