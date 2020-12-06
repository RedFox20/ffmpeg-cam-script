#!/usr/bin/python3
import os

video_device = "/dev/video0"

ffmpeg = "/usr/bin/ffmpeg -nostats -loglevel warning"

encode = f"{ffmpeg} -y -an -r ntsc -i {video_device}" \
     f" -flags2 local_header -aspect 1.77 -b:v 2200k" \
     f" -c:v libx264 -preset ultrafast -pix_fmt yuv420p" \
     f" -bf 0 -refs 0 -g 25 -bufsize 0" \
     f" -f matroska -"

raw = f"{ffmpeg} -y -an -r ntsc -i {video_device}" \
    f" -c:v libx264 -preset ultrafast -pix_fmt yuv420p -filter fps=fps=25 -f matroska -"

gst = f"gst-launch-1.0 v4l2src name=src device=/dev/video0"\
      " ! capsfilter caps=image/jpeg,width=640,height=480,framerate=25/1"\
      " ! jpegdec ! videoconvert"\
      " ! timeoverlay halignment=right valignment=bottom"\
      " ! ximagesink"

gst2 = f"gst-launch-1.0 videotestsrc ! ximagesink"

os.system(f"{gst}")
#os.system(f"{gst2}")

#os.system(f"{raw} | mplayer -")
#os.system(f"{encode} | mplayer -")
#os.system(f"{encode} | ffplay -nostats -fflags nobuffer -")