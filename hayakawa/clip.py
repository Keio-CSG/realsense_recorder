import argparse
import datetime
import time
import json
import os
import cv2
import numpy as np

from common import RecorderConfig

def save_clipped_data(recorded_colors: np.ndarray, recorded_depths: np.ndarray, out_dir: str, config: RecorderConfig):
    """
    録画したデータをRGB, Depth, JSONの3つに保存する
    """
    save_start = time.time()
    if os.path.exists(out_dir) is False:
        os.makedirs(out_dir)
    config.time_str = "c" + datetime.datetime.now().strftime('%Y-%m-%d-%H-%M-%S')
    config.depth_file = f"{config.time_str}-depth.npz"
    config.color_file = f"{config.time_str}-rgb.avi"
    config.time_sec = recorded_colors.shape[0] / config.frequency

    # JSONの保存
    with open(str(os.path.join(out_dir, f"{config.time_str}.json")), "w") as f:
        f.write(config.toJson())

    # Depthの保存
    depth_path = str(os.path.join(out_dir, config.depth_file))
    np.savez_compressed(
        depth_path,
        recorded_depths
    )

    # RGBの保存
    color_path = str(os.path.join(out_dir, config.color_file))
    fmt = cv2.VideoWriter_fourcc(*"mp4v")
    writer = cv2.VideoWriter(color_path, fmt, config.frequency, (config.width,config.height))
    for i in range(recorded_colors.shape[0]):
        writer.write(recorded_colors[i,:,:,:])
    writer.release()
    print(f"saved: {time.time() - save_start}s")

def clip_frame(color_file: str, depth_file: str, start: int, end: int, out_dir: str, config: RecorderConfig):
    """
    動画データをクリップして保存する
    """
    video = cv2.VideoCapture(color_file)

    depth_frames = np.load(depth_file)
    depth_frames = depth_frames[depth_frames.files[0]]
    depth_frames = depth_frames[start:end]

    current_frame = 0

    color_frame = None

    color_frames = np.zeros((end-start, config.height, config.width, 3), dtype=np.uint8)

    try:
        while True:
            ret, color_frame = video.read()
            if current_frame >= start and current_frame < end:
                color_frames[current_frame-start,:,:,:] = color_frame
            current_frame += 1
            if current_frame >= end:
                break
    finally:
        video.release()

    save_clipped_data(color_frames, depth_frames, out_dir, config)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("json", help="configuration file path")
    parser.add_argument("start", help="start frame", type=int)
    parser.add_argument("end", help="end frame", type=int)
    parser.add_argument("-o", "--out", default=".", help="out directory")
    args = parser.parse_args()
    json_path = args.json
    out_dir = args.out
    dir = os.path.split(os.path.abspath(json_path))[0]
    with open(json_path) as f:
        config_dic = json.load(f)
        config = RecorderConfig.fromJson(config_dic)
        print(config_dic)

    color_path = os.path.join(dir, config_dic["color_file"])
    depth_path = os.path.join(dir, config_dic["depth_file"])
    frequency = config_dic["frequency"]

    clip_frame(color_path, depth_path, args.start, args.end, out_dir, config)
