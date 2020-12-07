import os, sys, re, subprocess, base64

def create_h264rtp_command(source, extra_commands=None):
    """
    Generates a suitable Gstreamer H264 RTP Command

    source -- '/dev/video0' for live camera on linux

    source -- 'videotestsrc' for mocked fake source

    extra_commands -- extra commands between source and encoding: {src} ! {extra} ! {encode}
    """

    vid_src = ''
    if source == 'videotestsrc':
        vid_src = 'videotestsrc name=src'
    elif sys.platform.startswith('linux'):
        vid_src = f'v4l2src name=src device={source} do-timestamp=true'
    elif sys.platform == 'win32':
        vid_src = 'ksvideosrc name=src'
    
    if extra_commands:
        vid_src = f'{vid_src} ! {extra_commands}'

    encode = "x264enc name=ENC b-adapt=false bitrate=2200 ref=1 "\
            "speed-preset=superfast tune=zerolatency vbv-buf-capacity=100"

    rtp_pay = "rtph264pay name=RTP pt=96 mtu=1000"

    # encoder will grab frames from video source as fast as it can
    # and then submits it to the queue
    # with this setup, we are only limited by encoder speed
    return f"{vid_src} ! {encode} ! queue ! {rtp_pay}"


def run_udp_sink(gst_command, host, port):
    print(f"UDPSINK: {host}:{port}")
    return os.system(f"gst-launch-1.0 {gst_command} ! udpsink host={host} port={port}")


def _get_caps_keyvals(full_output, caps_key) -> dict:
    item = re.findall(f"{caps_key}.*$", full_output, re.MULTILINE)[0]
    item = item[len(caps_key):]
    caps = dict()
    for cap in item.split(', '):
        k,v = cap.split('=', maxsplit=1)
        k = k.strip()
        v = v.strip()
        if v.startswith('(int)'): v = v[5:]
        elif v.startswith('(string)'): v = v[8:]
        elif v.startswith('(uint)'): v = v[6:]
        #print(f"{k}={v}")
        caps[k] = v
    return caps


def get_rtp_caps(gst_command):
    """
    Looks up GstRtpH264Pay:*:GstPad:src:
    gst_command: gstreamer command without gst-launch
    """
    prepass_command = f"gst-launch-1.0 -v {gst_command} ! fakesink num-buffers=1"
    output = subprocess.check_output(prepass_command, shell=True).decode('utf-8')
    caps = _get_caps_keyvals(output, '/GstPipeline:pipeline0/GstRtpH264Pay:RTP.GstPad:src:')
    return caps


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

    sdp_string = f"""v=0
o=- 0 0 IN IP4 127.0.0.1
s=No Name
c=IN IP4 192.168.1.4
t=0 0
a=tool:libavformat 58.20.100
m=video 6666 RTP/AVP {pt}
a=rtpmap:{pt} {encname}/{clockrate}
a=fmtp:{pt} packetization-mode={pm}; sprop-parameter-sets={sps}; profile-level-id={prid}
"""
    sdp_base64_string = base64.b64encode(sdp_string.encode('ascii')).decode('ascii')
    return (sdp_string, sdp_base64_string)

