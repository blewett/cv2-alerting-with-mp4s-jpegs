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
import cv2
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
    roll = True
    while roll == True:
        roll = False

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
                    continue

                if rx.rectxrect(rt):
                    rt.addrect(rx)
                    rx.flag = False
                    roll = True
                    continue

# end of coalesce(rects):


# find comparison frame1 - loop until frames match - count == 0
def find_comparison_frame1(cap, frame_min_size_areas):
    count = 16
    repetitions = 0
    while count > 2:
        if repetitions > 4:
            break
        repetitions += 1
        #print("calculating comparison frame pass: " + str(repetitions))

        if cv2.waitKey(40) == ord('q'):
            exit(0)

        ret1,frame1 = cap.read()
        gray1 = cv2.cvtColor(frame1, cv2.COLOR_BGR2GRAY)
        gray1 = cv2.GaussianBlur(gray1, (21, 21), 0)

        if cv2.waitKey(40) == ord('q'):
            exit(0)

        ret2,frame2 = cap.read()
        gray2 = cv2.cvtColor(frame2, cv2.COLOR_BGR2GRAY)
        gray2 = cv2.GaussianBlur(gray2, (21, 21), 0)

        deltaframe = cv2.absdiff(gray1,gray2)
        threshold = cv2.threshold(deltaframe, 25, 255, cv2.THRESH_BINARY)[1]
        threshold = cv2.dilate(threshold, None)
        countour,heirarchy = cv2.findContours(threshold, cv2.RETR_EXTERNAL, 
                                              cv2.CHAIN_APPROX_SIMPLE)
        count = 0
        for i in countour:
            if cv2.contourArea(i) >= frame_min_size_areas:
                count += 1

    return frame2, gray2
    # end of find comparison frame1


def date_time_string():
    return datetime.datetime.now().strftime("%H:%M:%S  %d/%m/%Y")


def date_filename(prefix, postfix):
    f = datetime.datetime.now().strftime("%H-%M-%S--%d-%m-%Y")
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


def main():
    # create a VideoCapture object
    cap = cv2.VideoCapture(0)

    # check if camera opened successfully
    if (cap.isOpened() == False): 
        print("Unable to read camera feed")
        exit(0)

    # get the resolution of the frame
    frame_width = int(cap.get(3))
    frame_height = int(cap.get(4))
    if frame_scale != 1:
        frame_width = round(frame_width/frame_scale)
        frame_height = round(frame_height/frame_scale)

    # control variables - throttle frame display
    # frame_count_between_updates = 1
    frame_count = frame_count_between_updates

    # the minimum area that is a match for detection
    # frame_min_size_areas = 64

    # write_count for trailing - aproximately 1 second
    # frame_write_addon_count = 10

    # frame_trailing_writes is the frame count set to be written
    #  this is set AFTER motion is detected
    frame_trailing_writes = frame_write_addon_count

    # idle_count for detecting idle conditions and switching files
    # frame_idle_count = 24

    # number of repeated rectangles to trigger a frame1 reset
    # frame_reset_count = 32
    frame_reset_frame1 = False

    # variables for writing jpgs
    # frame_write_jpgs = True
    # frame_jpgs_min = 32
    # frame_scale = 1

    frames_jpgs_frame_count = 0
    frames_jpgs_width = 0
    frames_jpgs_height = 0

    #experiment with width
    #
    # setup to write mp4 video files
    #
    if frame_write_jpgs == False:
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        frame_video_filename = date_filename("motion", "mp4")
        video_file = cv2.VideoWriter(frame_video_filename, fourcc, 10,
                                 (frame_width, frame_height))
        print(frame_video_filename)
    frames_idle = 0
    frames_have_been_written = False

    # prime the reader - make sure that the frames are readable
    count = 0
    while count < frame_count_between_updates:
        ret1,frame1= cap.read()
        if cv2.waitKey(20) == ord('q'):
            exit(0)
        count += 1

    # read the first comparison frame
    (frame1, gray1) = find_comparison_frame1(cap, frame_min_size_areas)

    # rectangles array to check for stationary objects moved into the field
    frame1_rectangles = []

    while(True):
        ret2,frame2 = cap.read()
        gray2 = cv2.cvtColor(frame2, cv2.COLOR_BGR2GRAY)
        gray2 = cv2.GaussianBlur(gray2, (21, 21), 0)
        
        deltaframe=cv2.absdiff(gray1,gray2)
        threshold = cv2.threshold(deltaframe, 25, 255, cv2.THRESH_BINARY)[1]
        threshold = cv2.dilate(threshold,None)
        contour,heirarchy = cv2.findContours(threshold, cv2.RETR_EXTERNAL, 
                                              cv2.CHAIN_APPROX_SIMPLE)

        if frame_write_jpgs == True:
            frames_jpgs_frame_count += 1

        # collect and count the workable rectangles
        count = 0
        if len(contour) > 0:
            rects = []
            for element in contour:
                if (cv2.contourArea(element) < frame_min_size_areas):
                    continue

                (x, y, w, h) = cv2.boundingRect(element)
                rx = rectx(x, y, w, h)
                rects.append(rx)

            coalesce(rects)

            # count the workable contours
            count = 0
            for rt in rects:
                if rt.flag == True:
                    count += 1

        # there are active rectangles to process
        if (count > 0):
            frame_trailing_writes = frame_write_addon_count
            frame_reset_frame1 = False
            frames_idle = 0

            # for loop over contour rectangles
            for rx in rects:
                if rx.flag == False:
                    continue
 
                cv2.rectangle(frame2, (rx.x, rx.y),
                              (rx.x + rx.width, rx.y + rx.height),
                              (255, 0, 0), 2)

                # search for previous matching rectangles - reset frame1
                found = False
                for rt in frame1_rectangles:
                    #if rt.recteqrect(rx):
                    if rt.recteqrect(rx) or rt.rectinrect(rx):
                        rt.count += 1
                        if rt.count > frame_reset_count:
                            frame_reset_frame1 = True
                            found = True
                            break

                if found == False:
                    frame1_rectangles.append(rx)

            # end for loop over contours

            # background frame1 trigger happened - get a new background
            if frame_reset_frame1 == True:
                frame_reset_frame1 = False
                (frame1, gray1) = find_comparison_frame1(cap, frame_min_size_areas)
                frame1_rectangles = []
                frames_idle = 0

        # end if count > 0

        # label the frame with the date and time
        label_frame(frame2)

        # set frame_count_between_updates to throttle interactive output
        if frame_count >= frame_count_between_updates:
            cv2.imshow('window', frame2)
            frame_count = 0
        frame_count += 1

        if frame_write_jpgs == True:
            if count > 0 and frames_jpgs_frame_count > frame_jpgs_min:
                if frame_scale != 1:
                    frame2 = cv2.resize(frame2, (frame_width, frame_height))
                cv2.imwrite(date_filename("motion", "jpg"), frame2)
                frames_jpgs_frame_count = 0

            if cv2.waitKey(20) == ord('q'):
                    break
            continue
        # continue to while True if processing jpgs

        # if we are tracking motion write the frames out
        if frame_trailing_writes > 0:
            if frame_scale != 1:
                frame2 = cv2.resize(frame2, (frame_width, frame_height))
            video_file.write(frame2)
            frame_trailing_writes -= 1
            frames_have_been_written = True
        elif frame_one_file_only == False:
            frames_idle += 1
            frame1_rectangles = []

        # open the a new video file while idle
        if (frame_one_file_only == False and
            frames_have_been_written == True and
            frames_idle >= frame_idle_count):
            video_file.release()
            frame_video_filename = date_filename("motion", "mp4")
            video_file = cv2.VideoWriter(frame_video_filename, fourcc, 10,
                                         (frame_width, frame_height))
            print(frame_video_filename)
            frames_idle = 0
            frames_have_been_written = False

        if cv2.waitKey(20) == ord('q'):
            break

    # end while true
    
    if frame_write_jpgs == False:
        video_file.release()
        cap.release()
        if frames_have_been_written == False:
            os.remove(frame_video_filename)

    cv2.destroyAllWindows()

# argument parsing

#globals

# control variables - throttle frame display

# the count between screen updates - used to throtle output on slow machines
frame_count_between_updates = 0

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
frame_jpgs_min = 32
frame_scale = 1

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

    # frame_jpgs_min = 32
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

    # frame_scale = 1
    if (arg == "-scale-factor"):
        i += 1
        if i >= argc:
            print(prog + ": Missing arg needed for -scale-factor")
            exit(1)
        arg_string = sys.argv[i]
        """
        if arg_string.isdigit() == False:
            print(prog + ": the -scale-factor arg must be a number")
            exit(1)
        """
        arg_float = float(arg_string)
        if arg_float < 0:
            print(prog + ": the -scale-factor must be one or greater")
            exit(1)
        frame_scale = arg_float
        i += 1
        continue

    if (arg != "-h" and arg != "-help" and arg != "?" and arg != "-?"):
        print(prog + ": bad option: " + arg)

    print(prog + ": options")
    print()
    print("    -count-between-updates " + str(frame_count_between_updates))
    print("        set the count between screen updates.")
    print("        this is used to throttle output on slow machines.")
    print()
    print("    -idle-count " + str(frame_idle_count))
    print("        set the idle_count for detecting idle conditions.")
    print("        this is used to determine the end of a video capture.")
    print()
    print("    -min-size-areas " + str(frame_min_size_areas))
    print("        set the minimum area used for motion detection.")
    print()
    print("    -one-file")
    print("        put all of the detected frames in one video file.")
    print("        video files have the form: " + date_filename("motion", "mp4") + ".")
    print()
    print("    -reset-count " + str(frame_reset_count))
    print("        set the number of repeated rectangles to trigger a frame1 reset.")
    print("        frame1 has to be reset when stationary objects are added.")
    print()
    print("    -write-addon-count " + str(frame_write_addon_count))
    print("        set the write_count for frames trailing a detected motion.")
    print()
    print("    -write-jpgs")
    print("        put the detected \"motion\" frames in jpg files.")
    print("        jpg files have the form: " + date_filename("motion", "jpg") + ".")
    print("        set -min-size-areas to 256 to reduce the number of jpg files.")
    print()
    print("    -jpg-min-frames " + str(frame_jpgs_min))
    print("        set the minimum number of frames to be read prior to each jpg ")
    print("        file being written.  This throttles the number of jpg files.")
    print()
    print("    -scale-factor " + str(frame_scale))
    print("        this number is used to divide the hardware default frame size.")
    print("        this is used to reduce the size of the video and jpg files.")
    print()


    exit(1)

main()
