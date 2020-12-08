#!/usr/bin/python3
import os, pathlib

port = 5600

caps = pathlib.Path('caps.rtp').read_text()

caps = 'application/x-rtp,media=video,payload=96,encoding-name=H264,'\
       'packetization-mode=1,profile-level-id=64001e,'\
       'sprop-parameter-sets="Z2QAHqy0BQHtgLUGAQWlAAADAAEAAAMAPI8WLqA\\=\\,aO88sA\\=\\=",'\
       'ssrc=3448613135,timestamp-offset=753121922,seqnum-offset=19603,a-framerate=30'

udp = f'udpsrc port={port} ! {caps}'
clock = "clockoverlay halignment=right valignment=bottom time-format=\"%Y/%m/%d %H:%M:%S\""
gst_command = f'{udp} ! rtph264depay ! avdec_h264 ! {clock} ! autovideosink sync=false'
os.system(f'gst-launch-1.0 {gst_command}')
