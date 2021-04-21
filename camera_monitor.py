"""
  camera_monitor.py: Original work Copyright (C) 2021 by Blewett

MIT License

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

"""
# multiprocessing for email and uploads
import multiprocessing as mp
from multiprocessing import Queue
import time
import requests

# gmail related
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders

import webbrowser
import random
from getpass import getpass

# image processing
import cv2

# reporting and control
import datetime
import os
import sys

# rectangle class - includes sums, index, and flags
class rectx:
    def __init__(self, x, y, width, height):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.count = 0
        self.flag = True

    def setrect(self, x, y, width, height):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.count = 0
        self.flag = True

    def addpt(self, x, y):
        if (x < self.x):
            w = self.x - x
            self.x = x
            self.width += w
        elif (x > (self.x + self.width)):
            w = x - (self.x + self.width)
            self.width += w

        if (y < self.y):
            h = self.y - y
            self.y = y
            self.height += h
        elif (y > (self.y + self.height)):
            h = y - (self.y + self.height)
            self.height += h

    def addrect(self, r):
        self.addpt(r.x, r.y)
        self.addpt(r.x + r.width, r.y + r.height)

    def ptinrect(self, x, y):
        if (x < self.x):
            return False
        if (y < self.y):
            return False
        if (x > self.x + self.width):
            return False
        if (y > self.y + self.height):
            return False
        return True

    def rectinrect(self, r2):
        r1 = self

        if (r1.ptinrect(r2.x, r2.y) and 
            r1.ptinrect(r2.x + r2.width, r2.y + r2.height)):
            return True

        return False

    def rectxrect(self, r2):
        r1 = self
        if (r2.ptinrect(r1.x, r1.y) or
            r2.ptinrect(r1.x + r1.width, r1.y) or
            r2.ptinrect(r1.x, r1.y + r1.height) or
            r2.ptinrect(r1.x + r1.width, r1.y + r1.height)):
            return True

        if (r1.ptinrect(r2.x, r2.y) or
            r1.ptinrect(r2.x + r2.width, r2.y) or
            r1.ptinrect(r2.x, r2.y + r2.height) or
            r1.ptinrect(r2.x + r2.width, r2.y + r2.height)):
            return True

        return False

    def recteqrect(self, r):
        if (r.x != self.x):
            return False
        if (r.y != self.y):
            return False
        if (r.width != self.width):
            return False
        if (r.height != self.height):
            return False
        return True

    def rectpts(self):
        return self.x, self.y, self.x + self.width, self.y + self.height

    def print(self):
        print("self.x = " + str(self.x) +
              "  self.y = " + str(self.y) +
              "  self.width = " + str(self.width) +
              "  self.height = " + str(self.height))

    def printl(self, label):
        print(label +
              " x = " + str(self.x) +
              "  y = " + str(self.y) +
              "  width = " + str(self.width) +
              "  height = " + str(self.height) +
              "  count = " + str(self.count))

# end of rectangle class - includes count


# coalesce rectangles
def coalesce(rects):
    length = len(rects)
    outer = 0
    while outer < length:
        rx = rects[outer]
        outer += 1
        if rx.flag == False:
            continue

        inner = outer
        while inner < length:
            rt = rects[inner]
            inner += 1
            if rt.flag == False:
                continue

            if rt.rectinrect(rx):
                rx.flag = False
                break

            if rt.rectxrect(rx):
                if rx.width * rx.height >= rt.width * rt.height:
                    rt.flag = False
                    break
                elif rt.width * rt.height > rx.width * rx.height:
                    rx.flag = False

# end of coalesce(rects):

# find comparison frame1 - loop until frames match - count <= 2
def find_comparison_frame1(cap):
    count = 16
    repetitions = 0
    while count > 2:
        if repetitions > 4:
            break
        repetitions += 1
        #print("calculating comparison frame pass: " + str(repetitions))

        ret1,frame1 = cap.read()
        gray1 = cv2.cvtColor(frame1, cv2.COLOR_BGR2GRAY)
        gray1 = cv2.GaussianBlur(gray1, (21, 21), 0)

        ret2,frame2 = cap.read()
        gray2 = cv2.cvtColor(frame2, cv2.COLOR_BGR2GRAY)
        gray2 = cv2.GaussianBlur(gray2, (21, 21), 0)

        deltaframe = cv2.absdiff(gray1,gray2)
        threshold = cv2.threshold(deltaframe, 25, 255, cv2.THRESH_BINARY)[1]
        threshold = cv2.dilate(threshold, None)
        contours,heirarchy = cv2.findContours(threshold, cv2.RETR_EXTERNAL, 
                                              cv2.CHAIN_APPROX_SIMPLE)
        count = 0
        for i in contours:
            if cv2.contourArea(i) >= frame_min_size_areas:
                count += 1

    return frame2, gray2

# end of find comparison frame1


def skip_frames(cap, frame1, gray1, fr_area, fr):
    areas = []
    frames = []
    rectl = []
    area = 0

    for skips in range(1, frame_jpgs_capture):
        ret2,frame2 = cap.read()
        gray2 = cv2.cvtColor(frame2, cv2.COLOR_BGR2GRAY)
        gray2 = cv2.GaussianBlur(gray2, (21, 21), 0)
        
        deltaframe=cv2.absdiff(gray1,gray2)
        threshold = cv2.threshold(deltaframe, 25, 255, cv2.THRESH_BINARY)[1]
        threshold = cv2.dilate(threshold, None)
        contours,heirarchy = cv2.findContours(threshold, cv2.RETR_EXTERNAL, 
                                             cv2.CHAIN_APPROX_SIMPLE)

        # collect and count the workable rectangles
        count = 0
        if len(contours) > 0:
            rects = []
            area = 0
            for region in contours:
                area_tmp = cv2.contourArea(region)
                if (area_tmp < frame_min_size_areas):
                    continue
                area += area_tmp
                (x, y, w, h) = cv2.boundingRect(region)
                rx = rectx(x, y, w, h)
                rects.append(rx)

            areas.append(area)
            frames.append(frame2)
            rectl.append(rects)
        # end of if len(contours) > 0

    length = len(areas)
    which = 0
    if length != 0:
        for i in range(0, length):
            if areas[i] > area:
                which = i
                area = areas[i]

        if fr_area >= area:
            return fr

        rects = rectl[which]
        coalesce(rects)
        frame2 = frames[which]

        # draw the rectangles
        for rx in rects:
            if rx.flag == False:
                continue
            cv2.rectangle(frame2, (rx.x, rx.y),
                          (rx.x + rx.width, rx.y + rx.height),
                          (255, 0, 0), 1)
    # end of if length != 0

    label_frame(frame2)
    return frame2
# end of skip_frames

def date_time_string():
    t = datetime.datetime.now().strftime("%f")[:-5]
    f = datetime.datetime.now().strftime("%H-%M-%S." + t + "  %d/%m/%Y")
    return f

def date_filename(prefix, postfix):
    t = datetime.datetime.now().strftime("%f")[:-5]
    f = datetime.datetime.now().strftime("%H-%M-%S." + t + "--%d-%m-%Y")
    f = prefix + "." + f + "." + postfix
    return f

def label_frame(frame):
    # font type and dimensions
    font = cv2.FONT_HERSHEY_SIMPLEX 
    font_scale = 0.5
    font_thickness = 3
    (label_width, label_height), label_baseline = cv2.getTextSize("M", font, font_scale, font_thickness)

    x = 16
    y = 16
    x += label_width
    y += label_height + label_baseline

    ds = date_time_string()

    # a green and two pixels wide
    cv2.putText(frame, ds, (x,y), font, font_scale, (64, 255, 64), 2)

#
# main loop for monitoring the camera
#
def camera_monitor(queue):
    parse_args()
    send_args(queue)

    # create a VideoCapture object
    cap = cv2.VideoCapture(camera_number)

    # check if camera opened successfully
    if (cap.isOpened() == False): 
        print("VideoCapture cannot open the camera: " + str(camera_number))
        exit(0)

    # get the resolution of the frame
    frame_width = int(cap.get(3))
    frame_height = int(cap.get(4))
    if frame_scale != 1:
        frame_width = round(frame_width * frame_scale)
        frame_height = round(frame_height * frame_scale)

    # control variables - throttle frame display
    # frame_count_between_updates = 1
    frame_count = frame_count_between_updates

    # the minimum area that is a match for detection
    # frame_min_size_areas = 64

    # write_count for trailing - aproximately 1 second
    # frame_write_addon_count = 10

    # frame_trailing_writes is the frame count set to be written
    #  this is set AFTER motion is detected
    # frame_trailing_writes = frame_write_addon_count
    frame_trailing_writes = 10

    # idle_count for detecting idle conditions and switching files
    # frame_idle_count = 24

    # number of repeated rectangles to trigger a frame1 reset
    # frame_reset_count = 64
    # frame_reset_frame1 = False

    # variables for writing jpgs
    # frame_write_jpgs = True
    # frame_jpgs_min = 16
    # frame_scale = 1

    frames_jpgs_frame_count = 0
    frames_jpgs_width = 0
    frames_jpgs_height = 0

    frames_idle = 0
    frames_have_been_written = False

    # prime the reader - make sure that the frames are readable
    for i in range(8):
        ret1,frame1= cap.read()

    # set up to read the first comparison frame
    (frame1, gray1) = find_comparison_frame1(cap)
    frame_reset_frame1 = False

    # rectangles array to check for stationary objects moved into the field
    frame1_rectangles = []
    frame_reset_frame1 = False

    #
    # setup to write mp4 video files
    #
    if frame_write_jpgs == False:
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        frame_video_filename = date_filename("motion", "mp4")
        video_file = cv2.VideoWriter(frame_video_filename, fourcc, 10,
                                     (frame_width, frame_height))
        print(frame_video_filename)
    else:
        frame_video_filename = ""

    while True:
        if frame_reset_frame1 == True:
            frame_reset_frame1 = False
            (frame1, gray1) = find_comparison_frame1(cap)
            frame1_rectangles = []

        if cv2.waitKey(8) == ord('q'):
            break

        ret2,frame2 = cap.read()
        gray2 = cv2.cvtColor(frame2, cv2.COLOR_BGR2GRAY)
        gray2 = cv2.GaussianBlur(gray2, (21, 21), 0)
        
        deltaframe=cv2.absdiff(gray1,gray2)
        threshold = cv2.threshold(deltaframe, 25, 255, cv2.THRESH_BINARY)[1]
        threshold = cv2.dilate(threshold, None)
        contours,heirarchy = cv2.findContours(threshold, cv2.RETR_EXTERNAL, 
                                              cv2.CHAIN_APPROX_SIMPLE)

        if frame_write_jpgs == True:
            frames_jpgs_frame_count += 1

        # collect and count the workable rectangles
        count = 0
        area = 0
        if len(contours) > 0:
            rects = []
            for region in contours:
                area_tmp = cv2.contourArea(region)
                if (area_tmp < frame_min_size_areas):
                    continue
                area += area_tmp
                (x, y, w, h) = cv2.boundingRect(region)
                rx = rectx(x, y, w, h)
                rects.append(rx)

            coalesce(rects)

            # draw the rectangles - count the good ones
            for rx in rects:
                if rx.flag == False:
                    continue

                count += 1
                cv2.rectangle(frame2, (rx.x, rx.y),
                              (rx.x + rx.width, rx.y + rx.height),
                              (255, 0, 0), 1)

                # check for stationary objects
                if frame_reset_frame1 == False:
                    found = False
                    for rt in frame1_rectangles:
                        if rt.recteqrect(rx) or rt.rectinrect(rx):
                            rt.count += 1
                            if rt.count > frame_reset_count:
                                frame_reset_frame1 = True
                                break
                            found = True

                    if found == False:
                        frame1_rectangles.append(rx)
            # end of for rx in rects:
        # end of if len(contours) > 0

        # idle count is used for video files
        if count == 0:
            if frame_write_jpgs == False:
                frames_idle += 1
            if len(frame1_rectangles) > 0:
                frame1_rectangles = []
                frame_reset_frame1 = False

        if count > 0:
            frame_trailing_writes = frame_write_addon_count
            frames_idle = 0

        # label the frame with the date and time
        label_frame(frame2)

        # display the frame
        # set frame_count_between_updates to throttle interactive output
        if frame_no_display == False:
            if frame_count >= frame_count_between_updates:
                cv2.imshow('window', frame2)
                frame_count = 0
            # always 1
            frame_count += 1

        # process jpgs
        if count == 0 and frame_write_jpgs == True:
            continue
        if count > 0 and frame_write_jpgs == True:
            if frames_jpgs_frame_count > frame_jpgs_min:
                # skip the first few frames
                if frame_jpgs_capture > 0:
                    frame2 = skip_frames(cap, frame1, gray1, area, frame2)

                if frame_scale != 1:
                    frame2 = cv2.resize(frame2, (frame_width, frame_height))

                frame_video_filename = date_filename("motion", "jpg")
                cv2.imwrite(frame_video_filename, frame2)

                # send the file to be processed
                if frame_post_process == True:
                    queue.put(frame_video_filename)
                print(frame_video_filename)

                frames_jpgs_frame_count = 0
            continue
        # continue to while True if processing jpgs

        # if we are tracking motion write the frames out to the video file
        if frame_trailing_writes > 0:
            if frame_scale != 1:
                frame2 = cv2.resize(frame2, (frame_width, frame_height))
            video_file.write(frame2)
            frame_trailing_writes -= 1
            frames_have_been_written = True

        # open the a new video file while idle
        if (frame_one_file_only == False and
            frames_have_been_written == True and
            frames_idle >= frame_idle_count):
            video_file.release()

            # send the old one to be processed
            if frame_post_process == True:
                queue.put(frame_video_filename)

            frame_video_filename = date_filename("motion", "mp4")
            video_file = cv2.VideoWriter(frame_video_filename, fourcc, 10,
                                         (frame_width, frame_height))
            print(frame_video_filename)
            frames_idle = 0
            frames_have_been_written = False

    # end while true
    
    if frame_write_jpgs == False:
        video_file.release()
        cap.release()
        if (frames_have_been_written == False):
            os.remove(frame_video_filename)

    cv2.destroyAllWindows()

# end of camera_monitor(queue)

# the following three functions are small version of a corpus based
#   encryption system.  This version encodes only printable characters.
#   there is no backdoor to this.
# Blewett
def triple(p):
    # space through ~ - range of allowable characters
    charset_len = 126 - 32
    half_len = round(charset_len / 2)
    six_bits = 63
    seven_bits = 127
    eight_bits = 255

    x = 0
    for c in p:
        x = (x << 1) + ord(c)

    offset = (x & seven_bits)
    if offset < half_len:
        offset += half_len

    x = x >> 3
    reps = x & eight_bits
    if reps < half_len:
        reps += half_len

    x = x >> 3
    seed = (x & eight_bits) * offset * reps
    if seed < 2209:
        seed += half_len
        seed += seed * six_bits * offset * reps

#    print("s = " +  str(seed) + "  r = " +  str(reps) +
#          "  o = " +  str(offset))
    return seed, reps, offset

def encode(s, p):
    # space through ~ - range of allowable characters
    charset_len = 126 - 32

    (seed, reps, offset) = triple(p)

    random.seed(seed)
    for x in range(0, seed & 7):
        y = random.randint(32, 126)

    key = ""
    for x in range(0, reps):
        for c in (random.sample((range(32,127)), 127 - 32)):
            key = key + chr(c)
    keylen = len(key)
    if offset == 0 or offset >= keylen:
        offset = random.randint(0, keylen - 8)

    e = ""
    index = offset
    for c in s:
        x = index
        while True:
            if c == key[x]:
                ix = x - index
                # targets are no more than charset_len + delta apart
                #  where delta < charset_len
                if ix >= charset_len:
                    e = e + "~"
                    index += charset_len
                    ix = x - index
                e = e + chr(ix + 32)
                index = x
                break

            x += 1
            if x >= keylen:
                e = e + "~~"
                x = 0
                index = 0
    return e

def decode(e, p):
    # space to ~ - range of allowable characters
    charset_len = 126 - 32

    (seed, reps, offset) = triple(p)

    random.seed(seed)
    for x in range(0, seed & 7):
        y = random.randint(32, 126)

    key = ""
    for x in range(0, reps):
        for c in (random.sample((range(32,127)), 127 - 32)):
            key = key + chr(c)
    keylen = len(key)
    if offset == 0 or offset >= keylen:
        offset = random.randint(0, keylen - 8)

    d = ""
    index = offset
    lastc = ""
    for c in e:
        if c == '~':
            if lastc == '~':
                index = 0
                lastc = "check"
                continue
            else:
                index += charset_len
                lastc = c
            continue

        lastc = c
        x = index + ord(c) - 32
        d = d + key[x]
        index = x
    return d

# use gmail to send a file - thank you google
def gmail_image(image):

    fromaddr = gmail_login_name + "@gmail.com"
    toaddr = gmail_recipient

    # instance of MIMEMultipart
    msg = MIMEMultipart()
    
    # storing the senders email address
    msg['From'] = fromaddr
    
    # storing the receivers email address
    msg['To'] = toaddr
    
    # storing the subject
    msg['Subject'] = camera_name + ": " + image
    
    # string to store the body of the mail
    # body = "Body_of_the_mail"
    
    # attach the body with the msg instance
    # msg.attach(MIMEText(body, 'plain'))
    
    # open the file to be sent
    filename = image
    attachment = open(filename, "rb")
    
    # instance of MIMEBase and named as p
    p = MIMEBase('application', 'octet-stream')
    
    # To change the payload into encoded form
    p.set_payload((attachment).read())
    
    # encode into base64
    encoders.encode_base64(p)
    
    p.add_header('Content-Disposition', "attachment; filename= %s" % filename)
    
    # attach the instance 'p' to instance 'msg'
    msg.attach(p)
    
    # creates SMTP session
    s = smtplib.SMTP('smtp.gmail.com', 587)
    
    # start TLS for security
    s.starttls()
    
    # Authentication
    s.login(fromaddr, gmail_login_password)
    
    # Converts the Multipart msg into a string
    text = msg.as_string()
    
    # sending the mail
    s.sendmail(fromaddr, toaddr, text)
    
    # terminating the session
    s.quit()


# upload an image to a website
def upload_image(filename):
    #url = 'http://localhost:8181/upload.php'
    myobj = {'camera': camera_name}

    try:
        response = requests.post(camera_upload_link, data = myobj,
                                 files = { 'monitorFile': open(filename, "rb")})

        # Consider any status other than 2xx an error
        if not response.status_code // 100 == 2:
            print("upload problem: Unexpected response {}".format(response))
            return

    except requests.exceptions.RequestException as e:
        # A serious problem happened, like an SSLError or InvalidURL
        # print("upload problem: {}".format(e))
        print("upload problem: check if the server is running: " + 
              camera_upload_link)
        return

    # print the response text (the content of the requested file):
    print(response.text)
    os.remove(filename)


def camera_post_process(queue):
    recv_args(queue)
    while True:
        filename = queue.get()

        if gmail_login_name != "" and gmail_login_password != "" and gmail_recipient != "":
            gmail_image(filename)

        if camera_upload_link != "":
            upload_image(filename)

#
# globals
#

# control variables - throttle frame display

# the count between screen updates - used to throtle output on slow machines
frame_count_between_updates = 1
frame_no_display = False

# the minimum area that is a match for detection
frame_min_size_areas = 64

# the write_count for frames trailing a motion detection - aproximately 1 second
frame_write_addon_count = 10

# frame_trailing_writes is the frame count set to be written
#  this is set AFTER motion is detected
# frame_trailing_writes = frame_write_addon_count

# the idle_count for detecting idle conditions and switching video output files
frame_idle_count = 24

# the number of repeated rectangles to trigger a frame1 reset
frame_reset_count = 64

# flag to enable one file for all movement recording
frame_one_file_only = False

# variables for writing jpgs
frame_write_jpgs = False
frame_jpgs_min = 16
frame_jpgs_capture = 4
frame_scale = 1

# variables for transporting jpgs and mp4s
frame_post_process = False
camera_number = 0
camera_name = "camera1"
camera_upload_link = ""

# variables for mailing alerts through gmail
gmail_login_name = ""
gmail_login_password = ""
gmail_recipient = ""

def parse_args():
    global frame_count_between_updates
    global frame_no_display
    global frame_min_size_areas
    global frame_write_addon_count
    global frame_idle_count
    global frame_reset_count
    global frame_one_file_only
    global frame_write_jpgs
    global frame_jpgs_min
    global frame_jpgs_capture
    global frame_scale
    global frame_post_process
    global camera_number
    global camera_name
    global camera_upload_link
    global gmail_login_name
    global gmail_login_password
    global gmail_recipient

    argc = len(sys.argv)
    prog = sys.argv[0]

    i = 1
    while i < argc:
        arg = sys.argv[i]

        # the count between screen updates - used to throtle output on slow machines
        if (arg == "-count-between-updates"):
            i += 1
            if i >= argc:
                print(prog + ": Missing arg needed for -count-between-updates")
                exit(1)
            arg_string = sys.argv[i]
            if arg_string.isdigit() == False:
                print(prog + ": the -count-between-updates arg must be a number")
                exit(1)
            arg_int = int(arg_string)
            if arg_int < 0:
                print(prog + ": the -count-between-updates must be zero or greater")
                exit(1)
            frame_count_between_updates = arg_int
            i += 1
            continue

        # frame_no_display = True
        if (arg == "-no-display"):
            frame_no_display = True
            i += 1
            continue
    
        # the minimum area that is a match for motion detection
        if (arg == "-min-size-areas"):
            i += 1
            if i >= argc:
                print(prog + ": Missing arg needed for -min-size-areas")
                exit(1)
            arg_string = sys.argv[i]
            if arg_string.isdigit() == False:
                print(prog + ": the -min-size-areas arg must be a number")
                exit(1)
            arg_int = int(arg_string)
            if arg_int < 0:
                print(prog + ": the -min-size-areas must be zero or greater")
                exit(1)
            frame_min_size_areas = arg_int
            i += 1
            continue
    
        # the write_count for frames trailing a detected motion
        if (arg == "-write-addon-count"):
            i += 1
            if i >= argc:
                print(prog + ": Missing arg needed for -write-addon-count")
                exit(1)
            arg_string = sys.argv[i]
            if arg_string.isdigit() == False:
                print(prog + ": the -write-addon-count arg must be a number")
                exit(1)
            arg_int = int(arg_string)
            if arg_int < 0:
                print(prog + ": the -write-addon-count must be zero or greater")
                exit(1)
            frame_write_addon_count = arg_int
            i += 1
            continue
    
        # the idle_count for detecting idle conditions and switching files
        if (arg == "-idle-count"):
            i += 1
            if i >= argc:
                print(prog + ": Missing arg needed for -idle-count")
                exit(1)
            arg_string = sys.argv[i]
            if arg_string.isdigit() == False:
                print(prog + ": the -idle-count arg must be a number")
                exit(1)
            arg_int = int(arg_string)
            if arg_int < 0:
                print(prog + ": the -idle-count must be zero or greater")
                exit(1)
            frame_idle_count = arg_int0
            i += 1
            continue
    
        # the number of repeated rectangles to trigger a frame1 reset
        if (arg == "-reset-count"):
            i += 1
            if i >= argc:
                print(prog + ": Missing arg needed for -reset-count")
                exit(1)
            arg_string = sys.argv[i]
            if arg_string.isdigit() == False:
                print(prog + ": the -reset-count arg must be a number")
                exit(1)
            arg_int = int(arg_string)
            if arg_int < 0:
                print(prog + ": the -reset-count must be zero or greater")
                exit(1)
            frame_reset_count = arg_int
            i += 1
            continue
    
        # put all of the detected frames in one video file
        if (arg == "-one-file"):
            frame_one_file_only = True
            i += 1
            continue
    
        # frame_write_jpgs = True
        if (arg == "-write-jpgs"):
            frame_write_jpgs = True
            i += 1
            continue
    
        # frame_jpgs_min
        if (arg == "-jpg-min-frames"):
            i += 1
            if i >= argc:
                print(prog + ": Missing arg needed for -jpg-min-frames")
                exit(1)
            arg_string = sys.argv[i]
            if arg_string.isdigit() == False:
                print(prog + ": the -jpg-min-frames arg must be a number")
                exit(1)
            arg_int = int(arg_string)
            if arg_int < 0:
                print(prog + ": the -jpg-min-frames must be zero or greater")
                exit(1)
            frame_jpgs_min = arg_int
            i += 1
            continue
    
        # frame_jpgs_capture
        if (arg == "-jpg-capture-frames"):
            i += 1
            if i >= argc:
                print(prog + ": Missing arg needed for -jpg-capture-frames")
                exit(1)
            arg_string = sys.argv[i]
            if arg_string.isdigit() == False:
                print(prog + ": the -jpg-capture-frames arg must be a number")
                exit(1)
            arg_int = int(arg_string)
            if arg_int < 0:
                print(prog + ": the -jpg-capture-frames must be zero or greater")
                exit(1)
            frame_jpgs_capture = arg_int
            i += 1
            continue
    
        # frame_scale = 1
        if (arg == "-scale-factor"):
            i += 1
            if i >= argc:
                print(prog + ": Missing arg needed for -scale-factor")
                exit(1)
            arg_string = sys.argv[i]
    
            arg_float = float(arg_string)
            if arg_float < 0.25 or arg_float > 1.0:
                print(prog + ": the -scale-factor must be greater than 0.24 and less than or equal to one.")
                exit(1)
            frame_scale = arg_float
            i += 1
            continue
    
        if (arg == "-camera-name"):
            i += 1
            if i >= argc:
                print(prog + ": Missing arg needed for -camera-name")
                exit(1)
            arg_string = sys.argv[i]
            if len(arg_string) <= 0:
                print(prog + ": the -camera-name must at least one character long.")
                exit(1)
            camera_name = arg_string
            i += 1
            continue
    
        if (arg == "-camera-number"):
            i += 1
            if i >= argc:
                print(prog + ": Missing arg needed for -camera-number")
                exit(1)
            arg_string = sys.argv[i]
            if arg_string.isdigit() == False:
                print(prog + ": the -camera-number arg must be a number")
                exit(1)
            arg_int = int(arg_string)
            if arg_int < 0:
                print(prog + ": the -camera-number must be zero or greater")
                exit(1)
            camera_number = arg_int
            i += 1
            continue
    
        if (arg == "-upload-link"):
            i += 1
            if i >= argc:
                print(prog + ": Missing arg needed for -upload-link")
                exit(1)
            arg_string = sys.argv[i]
            if len(arg_string) < 10:
                print(prog + ": the -upload-link must at least ten characters long.")
                exit(1)
            camera_upload_link = arg_string
            frame_post_process = True
            i += 1
            continue
    
        # frame_gmail_config = False
        if (arg == "-gmail-browser-config"):
            webbrowser.open_new_tab("gmail-config.html")
            i += 1
            continue
    
        if (arg == "-gmail-info"):
            i += 1
            if i >= argc:
                print(prog + ": Missing arguments needed for -gmail-info")
                exit(1)
    
            arg_filename = sys.argv[i]
            i += 1
            af = ""
            ap = ""
            found = False
            for s in arg_filename:
                if s == ":":
                    found = True
                    continue
                if found == True:
                    ap = ap + s
                else:
                    af = af + s
    
            if found == True:
                arg_filename = af
                arg_password = ap
    
            try:
                f = open(arg_filename, "r")
            except IOError:
                print(prog + ": the -gmail-info file could not be read: \"" + arg_filename + "\"")
                exit()
    
            lines = f.readlines()
            f.close()
    
            if len(lines) != 3:
                print(prog + ": the -gmail-info file must contain three lines.")
                exit(1)
            
            if found == False:
                arg_password = getpass("Enter the password for " + arg_filename + ": ")
    
            if len(arg_password) <= 7:
                print(prog + ": the -gmail-info password must at least eight characters long.")
                exit(1)
    
            gmail_file_check = decode(lines[0].strip(), arg_password)
            if gmail_file_check != "qux":
                print(prog + ": the -gmail-info password does not match " + 
                      arg_filename + ".")
                exit(1)
    
            gmail_login_name = decode(lines[1].strip(), arg_password)
            print("The gmail login name is " + gmail_login_name + ".")
            gmail_login_password = decode(lines[2].strip(), arg_password)
            if gmail_login_name != "" and gmail_login_password != "" and gmail_recipient != "":
                frame_post_process = True
            continue
    
        if (arg == "-gmail-recipient"):
            i += 1
            if i >= argc:
                print(prog + ": Missing arg needed for -gmail-recipient")
                exit(1)
            arg_string = sys.argv[i]
            if len(arg_string) <= 8:
                print(prog + ": the -gmail-recipient must at least eight characters long.")
                exit(1)
                
            gmail_recipient = arg_string
            if gmail_login_name != "" and gmail_login_password != "" and gmail_recipient != "":
                frame_post_process = True
            i += 1
            continue
    
        # fall through as args do not match any of the options
        if (arg != "-h" and arg != "-help" and arg != "?" and arg != "-?"):
            print(prog + ": bad option: " + arg)
    
        print(prog + ": options")
        print()
        print("    -camera-name " + camera_name)
        print("        the -camera-name is the name of the directory in which the")
        print("        images will be stored when they are uploaded.")
        print()
        print("    -camera-number " + str(camera_number))
        print("        the -camera-number is the number of the camera or video")
        print("        device from which video will be read.  In most cases this")
        print("        number will be 0 (zero) as it is usually the first camera.")
        print()
        print("    -count-between-updates " + str(frame_count_between_updates))
        print("        set the count between display screen video updates.")
        print("        this is used to throttle output on slow machines.")
        print()
        print("    -idle-count " + str(frame_idle_count))
        print("        set the idle_count for detecting idle conditions.")
        print("        this is used to determine the end of a video capture.")
        print()
        print("    -jpg-capture-frames " + str(frame_jpgs_capture))
        print("        often the first frame when motion is detected is blurry.")
        print("        this sets the capture to be a number of frames after the")
        print("        motion is detected.")
        print()
        print("    -jpg-min-frames " + str(frame_jpgs_min))
        print("        set the minimum number of frames to be read prior to each jpg ")
        print("        file being written.  This throttles the number of jpg files.")
        print("        Depending on the system, there are about 20 frames per second.")
        print("        Setting this to 1200 would result in one frame per minute.")
        print()
        print("    -min-size-areas " + str(frame_min_size_areas))
        print("        set the minimum area used for motion detection.  differences")
        print("        less that this size will be ignored.")
        print()
        print("    -no-display")
        print("        do not display the video while this program is running.")
        print("        this is used to improve performance on slow machines.")
        print()
        print("    -one-file")
        print("        put all of the detected frames in one video file.")
        print("        video files have the form: " + date_filename("motion", "mp4") + ".")
        print("        use ffmpeg to convert to other video formats - webm or mov.")
        print("        ffmpeg -i motion*.mp4 -f webm m.webm")
        print()
        print("    -reset-count " + str(frame_reset_count))
        print("        set the number of repeated rectangles to trigger a frame1 reset.")
        print("        frame1 has to be reset when stationary objects are added or")
        print("        move into the field of view and subsequently stop.")
        print()
        print("    -scale-factor " + str(frame_scale))
        print("        this number is multiplied by the hardware default frame size.")
        print("        this is used to reduce the size of the video and jpg files.")
        print()
        print("    -write-addon-count " + str(frame_write_addon_count))
        print("        set the write count for frames to be added after motion is")
        print("        detected.  the added frames provide continuity between")
        print("        detections.")
        print()
        print("    -write-jpgs")
        print("        put the detected \"motion\" frames in jpg files.")
        print("        jpg files have the form: " + date_filename("motion", "jpg") + ".")
        print("        set -min-size-areas to 256 to reduce the number of jpg files.")
        print()
        print("    -upload-link http://yourserver:8181/upload.php")
        print("        the -upload-link is the server name and webpage to which the")
        print("        images will be uploaded.  if you are using a local server")
        print("        the link might be: http://localhost:8181/upload.php")
        print("        one can use multiple cameras and upload them to one website.")
        print()
        print("    -gmail-browser-config")
        print("        popup a browser window with two links to gmail.  One link")
        print("        is for logging into the gmail account.  The other link")
        print("        is for setting the less secure access used for sending")
        print("        email.  This access must be enabled to allow email to be")
        print("        sent from this program")
        print()
        print("    -gmail-info gmail.txt")
        print("        -gmail-info reads the login name and the login password from")
        print("        the named encrypted file.  The password for the encrypted file is")
        print("        read from the user (or it can included filename:password).  This")
        print("        avoids having the gmail password exposed on the command line and")
        print("        visible with process info.  We want to never have the gmail login")
        print("        and login password in the clear/open.")
        print()
        print("        -gmail-recipient must be set as well as -gmail-info if email")
        print("        is to be sent.  Run create_gmail_file.py to create an info file.")
        print()
        print("    -gmail-recipient some.one@gmail.com")
        print("        -gmail-recipient sets the recipient address for mail alerts that")
        print("        are sent when motion is detected.  -gmail-info must be set as")
        print("        well as -gmail-recipient if email is to be sent.")
        print()
    
        exit(1)

# end of parse_args()

# arguments are parsed once and sent via the queue to the other process
def print_args(where):
    print("where: " + where + "  gmail_login_name = " + gmail_login_name)
    print("where: " + where + "  gmail_login_password = " + gmail_login_password)
    print("where: " + where + "  gmail_recipient = " + gmail_recipient)
    print("where: " + where + "  camera_upload_link = " + camera_upload_link)
    print("where: " + where + "  camera_name = " + camera_name)

def send_args(queue):
    queue.put(gmail_login_name)
    queue.put(gmail_login_password)
    queue.put(gmail_recipient)
    queue.put(camera_upload_link)
    queue.put(camera_name)

def recv_args(queue):
    global camera_name
    global camera_upload_link
    global gmail_login_name
    global gmail_login_password
    global gmail_recipient

    gmail_login_name = queue.get()
    gmail_login_password = queue.get()
    gmail_recipient = queue.get()
    camera_upload_link = queue.get()
    camera_name = queue.get()


if __name__=="__main__":

    mp.set_start_method('spawn')
    queue = Queue()

    fx = mp.Process(target = camera_monitor, args = ((queue),))
    fx.daemon = True
    fx.start()

    gx = mp.Process(target = camera_post_process, args = ((queue),))
    gx.daemon = True
    gx.start()

    time.sleep(8)
    while True:
        print("Wait for processes to exit, continue, or quit")
        r = input("w(ait), c(continue), q(uit): ")
        if r == "q" or r == "x":
            exit(0)
        if r == "w":
            fx.join()
            print("waking, as if from a deep sleep")

#
