from enum import Enum, auto
from threading import Thread
from queue import Queue
import time
import datetime
import argparse
import os
import json
import pyrealsense2 as rs
import numpy as np
import cv2

class RecorderState(Enum):
    WAITING = auto()
    RECORDING = auto()

class RecorderConfig():
    """
    レコーダの設定(主にjsonで出力する用途)
    """
    def __init__(self, width: int, height: int, time_sec: float, frequency: int) -> None:
        self.width: int = width
        self.height: int = height
        self.time_sec: float = time_sec
        self.frequency: int = frequency
        self.time_str: str = None
        self.depth_file: str = None
        self.color_file: str = None

    def toJson(self) -> str :
        encoded = json.dumps({
            "width": self.width,
            "height": self.height,
            "time_sec": self.time_sec,
            "frequency": self.frequency,
            "time": self.time_str,
            "depth_file": self.depth_file,
            "color_file": self.color_file
        }, sort_keys=True, indent=2)
        return encoded

class SaveThread():
    def __init__(self, out_dir: str, config: RecorderConfig) -> None:
        self.thread = Thread(target=self.run)
        self.finished = False
        self.data_queue = Queue()
        self.config = config
        self.out_dir = out_dir
        self.max_frame = int(config.frequency * config.time_sec)
        self.recorded_colors = np.zeros((self.max_frame, config.height, config.width, 3), dtype=np.uint8)
        self.recorded_depths = np.zeros((self.max_frame, config.height, config.width), dtype=np.float)

    def start(self):
        self.thread.start()

    def finish(self):
        self.finished = True

    def run(self):
        frame_counter = 0
        while not self.finished:
            if self.data_queue.empty():
                time.sleep(0.03)
                continue
            received = self.data_queue.get()
            if received == "STOP":
                break
            color_image = received[0]
            depth_image = received[1]
            self.recorded_colors[frame_counter-1,:,:,:] = color_image
            self.recorded_depths[frame_counter-1,:,:] = depth_image
            frame_counter += 1

        self.save_recorded_data(self.recorded_colors, self.recorded_depths, self.out_dir, self.config)

    def save_recorded_data(self, recorded_colors: np.ndarray, recorded_depths: np.ndarray, out_dir: str, config: RecorderConfig):
        """
        録画したデータをRGB, Depth, JSONの3つに保存する
        """
        if os.path.exists(out_dir) is False:
            os.makedirs(out_dir)
        config.time_str = datetime.datetime.now().strftime('%Y-%m-%d-%H-%M-%S')
        config.depth_file = f"{config.time_str}-depth.npz"
        config.color_file = f"{config.time_str}-rgb.avi"

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
        print("finish")

def start_recorder(recorder_config: RecorderConfig, out_dir: str):
    """
    レコーダを表示する
    """
    width = recorder_config.width
    height = recorder_config.height
    frequency = recorder_config.frequency
    time_sec = recorder_config.time_sec
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

    save_thread = None
    # save_thread = SaveThread(out_dir, recorder_config)
    # save_thread.start()

    time_start = None

    top_bar_size = (56, 640, 3)
    
    prev_time = time.time()
    actual_fps = 0.0

    try:
        while True:
            frame_counter += 1
            if frame_counter % 30 == 0:
                actual_fps = 30 / (time.time() - prev_time)
                prev_time = time.time()

            frames = pipeline.wait_for_frames()
            # frames = align.process(frames)         

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
            elapsed_sec = frame_counter / frequency if recorder_state == RecorderState.RECORDING else 0.0
            top_bar = cv2.putText(
                top_bar, f"{width}x{height} {actual_fps:.1f}/{frequency}fps {elapsed_sec:.2f}/{time_sec:.2f}s",(10,50),
                cv2.FONT_HERSHEY_PLAIN, 2, (0,0,200), 3
            )

            if recorder_state == RecorderState.RECORDING:
                save_thread.data_queue.put((color_image, depth_image))
                if frame_counter == save_thread.max_frame:
                    print(f"save: {time.time() - time_start}s")
                    save_thread.data_queue.put("STOP")
                    recorder_state = RecorderState.WAITING

            color_image = cv2.resize(color_image, (640, 360), interpolation=cv2.INTER_NEAREST)
            depth_image = cv2.resize(depth_image, (640, 360), interpolation=cv2.INTER_NEAREST)
            depth_colormap = cv2.applyColorMap(
                cv2.convertScaleAbs(depth_image, alpha=0.08), cv2.COLORMAP_JET
            )

            cv2.namedWindow("Recorder", cv2.WINDOW_AUTOSIZE)
            cv2.imshow("Recorder", np.vstack((top_bar, color_image, depth_colormap)))

            k = cv2.waitKey(1)
            if k & 0xff == 27:
                cv2.destroyAllWindows()
                break
            elif k == ord("r") and recorder_state == RecorderState.WAITING:
                print("start recording")
                recorder_state = RecorderState.RECORDING
                save_thread = SaveThread(out_dir, recorder_config)
                save_thread.start()
                frame_counter = 0
                time_start = time.time()

    finally:
        pipeline.stop()
        save_thread.finish()

def resolve_resolution(width, height):
    """
    Realsenseで使える解像度が限られているため、解決する
    """
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
    parser.add_argument("-o", "--out", default=".", help="out directory")
    args = parser.parse_args()
    width = args.width
    height = args.height
    record_time_sec = args.time
    frequency = args.freq
    out_dir = args.out

    try:
        width, height = resolve_resolution(width, height)
        config = RecorderConfig(width, height, record_time_sec, frequency)
        start_recorder(config, out_dir)
    except BaseException as e:
        print(e)
