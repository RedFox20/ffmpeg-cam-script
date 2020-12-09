import os, re, sys, subprocess, base64

def create_h264rtp_command(source, extra_commands=None):
    """
    Generates a suitable Gstreamer H264 RTP Command

    source -- '/dev/video0' for live camera on linux

    source -- 'videotestsrc' for mocked fake source

    extra_commands -- extra commands between source and encoding: {src} ! {extra} ! {encode}
    """

    vid_src = ''
    if source == 'videotestsrc':
        vid_src = 'videotestsrc name=src pattern=ball'
    elif sys.platform.startswith('linux'):
        vid_src = f'v4l2src name=src device={source} do-timestamp=true'
    elif sys.platform == 'win32':
        vid_src = 'ksvideosrc name=src'
    
    if extra_commands:
        vid_src = f'{vid_src} ! {extra_commands}'

    # aud=false  We don't need these AccessUnitDelimiters
    # b-adapt=true Automatically pick B-frame 
    # byte-stream=true Enable Annex-B
    # ref=# Number of reference frames
    # vbv-buf-capacity=100 Size of VBV buffer in milliseconds
    # key-int-max=# max distance between IDR frames
    encode = "x264enc name=ENC aud=false b-adapt=true byte-stream=true "\
             "key-int-max=5 ref=1 "\
             "bitrate=2200 speed-preset=superfast tune=zerolatency vbv-buf-capacity=100"

    rtp_pay = "rtph264pay name=RTP pt=96 mtu=1000"

    # encoder will grab frames from video source as fast as it can
    # and then submits it to the queue
    # with this setup, we are only limited by encoder speed
    return f"{vid_src} ! {encode} ! queue ! {rtp_pay}"


def run_udp_sink(gst_command, host, port):
    print(f"UDPSINK: {host}:{port}")
    return os.system(f"gst-launch-1.0 {gst_command} ! udpsink host={host} port={port}")


def _set_caps_keyvals(destination:dict, full_output, caps_key):
    caps = re.findall(f"{caps_key}.*$", full_output, re.MULTILINE)[0]
    caps = caps[len(caps_key):]
    for cap in caps.split(', '):
        k,v = cap.split('=', maxsplit=1)
        k = k.strip()
        v = v.strip()
        if v.startswith('(int)'): v = v[5:]
        elif v.startswith('(string)'): v = v[8:]
        elif v.startswith('(uint)'): v = v[6:]
        elif v.startswith('(fraction)'): v = v[10:]
        #print(f"{k}={v}")
        destination[k] = v


def _get_caps_string(full_output, caps_key):
    caps = re.findall(f"{caps_key}.*$", full_output, re.MULTILINE)[0]
    caps = caps[len(caps_key):]
    caps_string = caps.replace(' caps = ', '')
    return caps_string


def get_rtp_caps(gst_command):
    """
    Looks up GstRtpH264Pay:*:GstPad:src:
    gst_command: gstreamer command without gst-launch
    """
    prepass_command = f"gst-launch-1.0 -v {gst_command} ! fakesink num-buffers=1"
    output = subprocess.check_output(prepass_command, shell=True).decode('utf-8')
    print(output)
    caps_keyvals = dict()
    _set_caps_keyvals(caps_keyvals, output, '/GstPipeline:pipeline0/GstX264Enc:ENC.GstPad:src:')
    _set_caps_keyvals(caps_keyvals, output, '/GstPipeline:pipeline0/GstRtpH264Pay:RTP.GstPad:src:')
    caps_string = _get_caps_string(output, '/GstPipeline:pipeline0/GstRtpH264Pay:RTP.GstPad:src:')
    return (caps_keyvals, caps_string)


def generate_sdp_string(caps:dict) -> str:
    """
    Generates an SDP string and also encodes it as Base64
    -> (sdp_string, sdp_base64_string)
    """
    pt = caps['payload']
    pm = caps['packetization-mode']
    sps = caps['sprop-parameter-sets']
    prid = caps['profile-level-id'].capitalize()
    encname = caps['encoding-name']
    clockrate = caps['clock-rate']
    framerate = caps['a-framerate']
    width = caps['width']
    height = caps['height']

    # gstreamer outputs an escaped string, so we need to unescape:
    # "Z2QAHqy0BQHtgLUGAQWlAAADAAEAAAMAPI8WLqA\\=\\,aO88sA\\=\\="
    sps = sps.strip('"').replace('\\=', '=').replace('\\,', ',')

    sdp_string = f"""v=0
o=- 0 0 IN IP4 127.0.0.1
s=No Name
c=IN IP4 192.168.1.4
t=0 0
a=tool:libavformat 58.20.100
m=video 6666 RTP/AVP {pt}
a=rtpmap:{pt} {encname}/{clockrate}
a=fmtp:{pt} packetization-mode={pm}; sprop-parameter-sets={sps}; profile-level-id={prid}
a=framesize:{pt} {width}-{height}
a=framerate:{framerate}
"""
    sdp_base64_string = base64.b64encode(sdp_string.encode('ascii')).decode('ascii')
    return (sdp_string, sdp_base64_string)

