#!/usr/bin/python3
import os, json, requests, subprocess, pathlib
import gstutils

kratthost = '13.49.97.30'
krattapi = f'{kratthost}:5555/api'

drone_uid = 'krattowl_mock'
drone_name = 'Krattowl Mocked Test Feed'
session_secret = 'RJ9hg0WxVdm8z5ofaAs3wKvQYcOS72FErUGCHBLTuMpDN4q1yliI6bPnXZejkt'
camera_sdp = '<to be generated>'

gst_command = gstutils.create_h264rtp_command('videotestsrc', 'video/x-raw,width=640,height=480')
print(f'Gstreamer Command: {gst_command}\n')
caps, caps_string = gstutils.get_rtp_caps(gst_command)
print(f'RTP caps = {caps}\n')
sdp_string, camera_sdp = gstutils.generate_sdp_string(caps)
print(f"Generated SDP:\n{sdp_string}")
pathlib.Path('camera.sdp').write_text(sdp_string)
pathlib.Path('caps.rtp').write_text(caps_string)

def main():
    registered = False
    try:
        print(f"Send REGISTER uid:{drone_uid} secret:{session_secret}")
        register_json = {'uid':drone_uid,'name':drone_name,'secret':session_secret,'camera_sdp':camera_sdp}
        register_resp = requests.post(f'http://{krattapi}/drone_register', json=register_json).json()
        print("Register Response: ", register_resp)
        registered = register_resp['success']
        if not registered:
            print(f"REGISTER FAILED with MESSAGE: {register_resp['message']}")
            return

        camera_port = register_resp['camera_port']
        gstutils.run_udp_sink(gst_command, kratthost, camera_port)
    except KeyboardInterrupt:
        pass
    finally:
        if registered:
            unregister_json = {'uid':drone_uid,'secret':session_secret}
            print(f"Send UNREGISTER {unregister_json}")
            unregister_result = requests.post(f'http://{krattapi}/drone_unregister', json=unregister_json)
            print("Unregister Response: ", unregister_result.json())

main()
