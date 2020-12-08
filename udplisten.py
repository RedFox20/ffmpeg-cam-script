#!/usr/bin/python3
import os, pathlib

port = 5600
caps = 'application/x-rtp,media=video,payload=96,encoding-name=H264'
#caps = pathlib.Path('caps.rtp').read_text()

udp = f'udpsrc port={port} ! {caps}'
clock = "clockoverlay halignment=right valignment=bottom time-format=\"%Y/%m/%d %H:%M:%S\""
gst_command = f'{udp} ! rtph264depay ! avdec_h264 ! {clock} ! autovideosink sync=false'
os.system(f'gst-launch-1.0 {gst_command}')
