import os, re, json, requests, subprocess, base64, pathlib

kratthost = '13.49.97.30'
krattapi = f'{kratthost}:5555/api'

drone_uid = 'krattowl_mock'
drone_name = 'Krattowl Mocked Test Feed'
session_secret = 'RJ9hg0WxVdm8z5ofaAs3wKvQYcOS72FErUGCHBLTuMpDN4q1yliI6bPnXZejkt'
camera_sdp = '<to be generated>'

gst = "gst-launch-1.0 -v"
gst_test = f"videotestsrc ! video/x-raw,width=640,height=480"
enc_opt = "b-adapt=false bitrate=2200 ref=1 speed-preset=superfast vbv-buf-capacity=100"
encode  = f"x264enc name=ENC {enc_opt}"
rtp_pay = "rtph264pay name=RTP pt=96 mtu=1000 config-interval=1"

gst_enc_rtp = f"{gst} {gst_test} ! {encode} ! {rtp_pay}"
prepass_command = f"{gst_enc_rtp} ! fakesink num-buffers=1"

def get_caps_keyvals(full_output, caps_key) -> dict:
    item = re.findall(f"{caps_key}.*$", output, re.MULTILINE)[0]
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

output = subprocess.check_output(prepass_command, shell=True).decode('utf-8')
caps = get_caps_keyvals(output, '/GstPipeline:pipeline0/GstRtpH264Pay:RTP.GstPad:src:')
print(caps)
print()

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
camera_sdp = base64.b64encode(sdp_string.encode('ascii')).decode('ascii')

print(f"GENERATED SDP:\n{sdp_string}")
print(f"BASE64 SDP: {camera_sdp}")
pathlib.Path('camera.sdp').write_text(sdp_string)

def main():
    registered = False
    try:
        print("Send REGISTER")
        register_json = {'uid':drone_uid,'name':drone_name,'secret':session_secret,'camera_sdp':camera_sdp}
        register_resp = requests.post(f'http://{krattapi}/drone_register', json=register_json).json()
        print("Register Response: ", register_resp)
        registered = register_resp['success']
        if not registered:
            print(f"REGISTER FAILED with MESSAGE: {register_resp['message']}")
            return

        camera_port = register_resp['camera_port']
        print(f"camera UDPSINK: {kratthost}:{camera_port}")
        os.system(f"{gst_enc_rtp} ! udpsink host={kratthost} port={camera_port}")
    except KeyboardInterrupt:
        pass
    finally:
        if registered:
            print("Send UNREGISTER")
            unregister_json = {'uid':drone_uid,'secret':session_secret}
            unregister_result = requests.post(f'http://{krattapi}/drone_unregister', json=unregister_json)
            print("Unregister Response: ", unregister_result.json())

main()
