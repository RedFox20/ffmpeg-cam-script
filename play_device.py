#!/usr/bin/python3
import os
import gstutils

#os.system(f'gst-launch-1.0 autovideosrc ! d3dvideosink sync=false')
#fpsdisplaysink
gst_command = gstutils.create_h264rtp_command(
      source='autovideosrc',
      extra_commands='')

clock = "clockoverlay halignment=right valignment=bottom time-format=\"%Y/%m/%d %H:%M:%S\""
display = f'rtph264depay ! avdec_h264 ! {clock} ! autovideosink sync=false'
os.system(f'gst-launch-1.0 {gst_command} ! {display}')
exit()


#v4l2-ctl -d /dev/v4l/by-id/usb-MACROSILICON_AV_TO_USB2.0_20150130-video-index0 --list-formats
#/dev/v4l/by-id/usb-MACROSILICON_AV_TO_USB2.0_20150130-video-index0
#/dev/v4l/by-id/usb-fushicai_usbtv007_300000000002-video-index0
video_device = "/dev/video0"

thermal_cam = "/dev/v4l/by-id/usb-MACROSILICON_AV_TO_USB2.0_20150130-video-index0"
rgb_cam = "/dev/v4l/by-id/usb-fushicai_usbtv007_300000000002-video-index0"

# v4l2h264enc
gst = "gst-launch-1.0 -v"
gst_thr = f"v4l2src name=src device={thermal_cam} do-timestamp=true"\
       " ! capsfilter caps=image/jpeg,width=640,height=480,framerate=25/1"\
       " ! jpegdec"

gst_rgb = f"v4l2src name=src device={rgb_cam} do-timestamp=true"\
      " ! \"video/x-raw,format=YUY2,width=800,height=600,framerate=20/1\""

gst_test = f"videotestsrc ! video/x-raw,width=640,height=480"

imagesink = f"videoconvert ! {clock} ! autovideosink sync=false"


############
# intra-refresh=true # lower latency???
enc_opt = "b-adapt=false bitrate=2200 ref=1"\
          " speed-preset=superfast vbv-buf-capacity=100"
encode_x264  = f"x264enc {enc_opt} ! h264parse config-interval=-1"

enc_opt = "target-bitrate=2200 quant-b-frames=0"
encode_omx = f"omxh264enc {enc_opt}"

enc_opt = "max-bframes=0 bitrate=2200000"
encode_av264 = f"avenc_h264_omx {enc_opt}"

encode = encode_x264
###########

# aggregate-mode=zero-latency
rtp_pay = "rtph264pay pt=96 mtu=1000 config-interval=1"
udpsink = "udpsink host=192.168.1.4 port=6666"
udpsrc = "udpsrc port=6666"

rtp_depay_decode = "rtph264depay ! avdec_h264"

#os.system(f"{gst} {gst_test} ! {encode} ! {rtp_pay} ! {udpsink}")
os.system(f"{gst} {gst_test} ! {imagesink}")

#os.system(f"{udpsrc} ! {rtp_depay_decode} ! {imagesink}")
#os.system(f"{gst_rgb} ! {imagesink}")
#os.system(f"{}")

#os.system(f"{raw} | mplayer -")
#os.system(f"{encode} | mplayer -")
#os.system(f"{encode} | ffplay -nostats -fflags nobuffer -")

#gst-launch -v udpsrc port=5000 caps="<CAPS_FROM_SERVER>" ! rtph264depay ! ffdec_h264 ! xvimagesink

# easycap = "/root/easycap-somagic-linux/somagic-capture"\
#           " --sync=1 --iso-transfers 20 -B 149 -C 72 --luminance 2 --lum-aperture 3"
# gste = f"{easycap} |"\
#       "gst-launch-1.0 fdsrc fd=0"\
#       " ! capsfilter caps=image/jpeg,width=640,height=480,framerate=25/1"\
#       " ! jpegdec ! videoconvert ! videoscale "\
#       " ! clockoverlay halignment=right valignment=bottom time-format=\"%Y/%m/%d %H:%M:%S\""\
#       " ! ximagesink sync=false"


# ffmpeg = "/usr/bin/ffmpeg -nostats -loglevel warning"

# encode = f"{ffmpeg} -y -an -r ntsc -i {video_device}" \
#      f" -flags2 local_header -aspect 1.77 -b:v 2200k" \
#      f" -c:v libx264 -preset ultrafast -pix_fmt yuv420p" \
#      f" -bf 0 -refs 0 -g 25 -bufsize 0" \
#      f" -f matroska -"

# raw = f"{ffmpeg} -y -an -r ntsc -i {video_device}" \
#     f" -c:v libx264 -preset ultrafast -pix_fmt yuv420p -filter fps=fps=25 -f matroska -"
