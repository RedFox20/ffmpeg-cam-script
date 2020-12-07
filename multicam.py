#!/usr/bin/python3
import os, pathlib, argparse
import gstutils

#########
# Example usage:
# ./multicam.py --src /dev/video0 --udp 192.168.1.4:6666 --sdp=/root/sdp.sdp
#
parser = argparse.ArgumentParser()
parser.add_argument('--src', type=str, help='set the camera source',
                    default='/dev/v4l/by-id/usb-MACROSILICON_AV_TO_USB2.0_20150130-video-index0')
parser.add_argument('--udp', type=str, help='udp destination ip:port',
                    default='192.168.1.4:6666')
parser.add_argument('--sdp', type=str, help='set the SDP file output path',
                    default='camera.sdp')
args = parser.parse_args()

source = args.src
extra_commands = None
if 'usb-MACROSILICON_AV_TO_USB2.0_20150130' in source:
    extra_commands = 'capsfilter caps=image/jpeg,width=640,height=480,framerate=25/1 ! jpegdec'
elif source == 'videotestsrc':
    extra_commands = 'video/x-raw,width=640,height=480'

gst_command = gstutils.create_h264rtp_command(source, extra_commands)
print(f'Gstreamer Command: {gst_command}\n')

caps = gstutils.get_rtp_caps(gst_command)
print(f'Caps: {caps}\n')
sdp_string, camera_sdp = gstutils.generate_sdp_string(caps)

print(f"Generated SDP:\n{sdp_string}")
pathlib.Path(args.sdp).write_text(sdp_string)

host, port = args.udp.split(':')
gstutils.run_udp_sink(gst_command, host, port)
