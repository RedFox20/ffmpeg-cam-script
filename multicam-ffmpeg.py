import os
import concurrent.futures

def start_stream_h264(video_device, rtp_address, sdp_file):
    print(f"Starting stream dev={video_device} rtp={rtp_address} sdp={sdp_file}", flush=True)

    ffmpeg = "/usr/bin/ffmpeg -nostats -loglevel warning"

    # -filter:v fps=fps=10 
    # This encodes the video stream and forwards output to pipe
    encode = f"{ffmpeg} -y -an -r ntsc -i {video_device} " \
             f"-flags2 local_header -aspect 1.77 -b:v 2200k " \
             f"-c:v libx264 -preset ultrafast -pix_fmt yuv420p " \
             f"-f matroska - "

    # Takes video from input pipe and transfers over RTP
    transfer = f"{ffmpeg} -i - -vcodec copy -vbsf h264_mp4toannexb -an " \
               f"-f rtp -sdp_file {sdp_file} \"{rtp_address}?pkt_size=1000\""

    result = os.system(f"{encode} | {transfer}")
    print(f"Stopped stream dev={video_device} with result: {result}", flush=True)
    return result

def add_stream(executor, video_device, rtp_address, sdp_file):
    return executor.submit(start_stream_h264, video_device, rtp_address, sdp_file)

with concurrent.futures.ThreadPoolExecutor() as e:
    tasks = [
        add_stream(e, "/dev/video0", "rtp://192.168.1.4:6666", "/root/sdp.sdp")
    ]
    for t in tasks:
        t.result()
