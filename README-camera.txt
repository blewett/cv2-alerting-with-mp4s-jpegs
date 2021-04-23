These are the steps for running and testings the camera software
downloaded as a zip file from github.com.  These steps are in Windows
10 jargon.  Substitute "/" for "\" and "terminal" for "cmd" for Linux
and Macs.

0. This system uses python3 and php.  This works well on Linux, Apple
   macs, and Windows 10.  One has to install python3 and php on each
   of those systems - easy.  On Linux systems (often Ubuntu) one uses
   apt install.  On macs, one uses brew to install python after
   installing xcode.  xcode is free.  xcode ships with php.  On
   Windows 10, one uses the following links:

    https://www.python.org/downloads
    https://pypi.org/project/opencv-python
    https://windows.php.net/download

   python3 will complain about missing pacakges.  Install them with
   pip3:

    pip3 install opencv-python
    pip3 install request

1. Create a Desktop camera folder
   right click on the Desktop and select New -> folder
   we commonly use "camera" as the name of the folder
   extract the zip file to the camera folder

2. Start a command prompt window by entering cmd in the search bar and
   move to the camera directory.

  cd Desktop\camera\cv2-alerting-with-mp4s-jpegs-main

3. Run the camera monitor with python3 and write jpeg files.

  python3 camera_monitor.py -write-jpgs

4. To run an php http server, start a command prompt window by
   entering cmd in the search bar and move to the camera
   php-http-server direcotry

  cd Desktop\camera\cv2-alerting-with-mp4s-jpegs-main\php-http-server

5. Start a php server in the directory from above.

  php -S localhost:8181

   The php web server will now continue to run in this window.

6. Run the monitor with the upload link to archive the images.

  python3 camera_monitor.py -upload-link http://localhost:8181/upload.php

   Images will now be uploaded to the server.
