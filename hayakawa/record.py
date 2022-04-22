from enum import Enum, auto
import time
import datetime
import argparse
import os
import pyrealsense2 as rs
import numpy as np
import cv2

class RecorderState(Enum):
    WAITING = auto()
    COUNTING = auto()
    RECORDING = auto()

def save_recorded_data(recorded_colors: np.ndarray, recorded_depths: np.ndarray, out_dir: str):
    if os.path.exists(out_dir) is False:
        os.makedirs(out_dir)
    date_str = datetime.datetime.now().strftime('%Y-%m-%d-%H-%M-%S')
    depth_path = str(os.path.join(out_dir, f"{date_str}-depth.npz"))
    color_path = str(os.path.join(out_dir, f"{date_str}-rgb.avi"))
    np.savez_compressed(
        depth_path,
        recorded_depths.astype(np.int16)
    )
    fmt = cv2.VideoWriter_fourcc(*"mp4v")
    writer = cv2.VideoWriter(color_path, fmt, 30.0, (640,360))
    for i in range(recorded_colors.shape[0]):
        writer.write(recorded_colors[i,:,:,:])
    writer.release()

def start_recorder(width: int, height: int, time_sec: float, frequency: int, out_dir: str):
    # ストリーム(Depth/Color)の設定
    config = rs.config()
    config.enable_stream(rs.stream.color, width, height, rs.format.bgr8, frequency)
    config.enable_stream(rs.stream.depth, width, height, rs.format.z16, frequency)

    # ストリーミング開始
    pipeline = rs.pipeline()
    profile = pipeline.start(config)

    # Alignオブジェクト生成
    align_to = rs.stream.color
    align = rs.align(align_to)

    recorder_state = RecorderState.WAITING
    frame_counter = 0

    recorded_colors = np.zeros((int(frequency*time_sec), height, width, 3), dtype=np.uint8)
    recorded_depths = np.zeros((int(frequency*time_sec), height, width))
    time_start = None

    top_bar_size = (56, 640, 3)

    try:
        while True:
            frames = pipeline.wait_for_frames()
            frames = align.process(frames)

            frame_counter += 1

            color_frame = frames.get_color_frame()
            depth_frame = frames.get_depth_frame()
            if not depth_frame or not color_frame:
                print("********* frame is dropped **********")
                continue

            color_image = np.asanyarray(color_frame.get_data())
            depth_image = np.asanyarray(depth_frame.get_data())

            depth_colormap = cv2.applyColorMap(
                cv2.convertScaleAbs(depth_image, alpha=0.08), cv2.COLORMAP_JET
            )

            top_bar = np.zeros(top_bar_size, dtype=np.uint8)
            top_bar = cv2.putText(
                top_bar, f"{width}x{height}",(400,50),
                cv2.FONT_HERSHEY_PLAIN, 2, (0,0,200), 3
            )

            if recorder_state == RecorderState.COUNTING:
                count_down = 3 - (frame_counter // frequency)
                top_bar = cv2.putText(
                    top_bar, f"{int(count_down)}",(10,50),
                    cv2.FONT_HERSHEY_PLAIN, 2, (0,0,200), 3
                )
                if count_down == 0:
                    print("start recording")
                    recorder_state = RecorderState.RECORDING
                    frame_counter = 0
                    time_start = time.time()
            elif recorder_state == RecorderState.RECORDING:
                recorded_colors[frame_counter-1,:,:,:] = color_image
                recorded_depths[frame_counter-1,:,:] = depth_image
                top_bar = cv2.putText(
                    top_bar, f"REC",(10,50),
                    cv2.FONT_HERSHEY_PLAIN, 2, (0,0,200), 3
                )
                if frame_counter == recorded_colors.shape[0]:
                    print(f"save: {time.time() - time_start}s")
                    save_recorded_data(recorded_colors, recorded_depths, out_dir)
                    recorder_state = RecorderState.WAITING
            else:
                top_bar = cv2.putText(
                    top_bar, f"press r",(10,50),
                    cv2.FONT_HERSHEY_PLAIN, 2, (0,0,200), 3
                )

            color_image = cv2.resize(color_image, (640, 360))
            depth_colormap = cv2.resize(depth_colormap, (640, 360))

            cv2.namedWindow("Recorder", cv2.WINDOW_AUTOSIZE)
            cv2.imshow("Recorder", np.vstack((top_bar, color_image, depth_colormap)))

            k = cv2.waitKey(1)
            if k & 0xff == 27:
                cv2.destroyAllWindows()
                break
            elif k == ord("r") and recorder_state == RecorderState.WAITING:
                print("count start")
                recorder_state = RecorderState.COUNTING
                frame_counter = 0
    finally:
        pipeline.stop()

def resolve_resolution(width, height):
    if width is None and height is None:
        return 640, 360
    if width == 424:
        if height is None or height == 240:
            return width, 240
    if width == 640:
        if height is None:
            return width, 360
        if height == 360 or height == 480:
            return width, height
    if width == 848:
        if height is None or height == 480:
            return width, 480
    if width == 1280:
        if height is None or height == 720:
            return width, 720

    height_str = height if height is not None else "-"
    raise ValueError(f"Not Supported Resolution: ({width},{height_str})")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-w", "--width", type=int, default=640, help="horizontal resolution")
    parser.add_argument("--height", type=int, default=None, help="vertical resolution")
    parser.add_argument("-t", "--time", type=float, default=10.0, help="recording time in second")
    parser.add_argument("-f", "--freq", type=int, default=30, help="camera frequency")
    parser.add_argument("-o", "--out", default="", help="out directory")
    args = parser.parse_args()
    width = args.width
    height = args.height
    record_time_sec = args.time
    frequency = args.freq
    out_dir = args.out

    try:
        width, height = resolve_resolution(width, height)
        start_recorder(width, height, record_time_sec, frequency, out_dir)
    except BaseException as e:
        print(e)
