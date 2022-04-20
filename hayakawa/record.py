from enum import Enum, auto
import time
import datetime
import pyrealsense2 as rs
import numpy as np
import cv2

FRAMES_PER_SECOND = 30

# ストリーム(Depth/Color)の設定
config = rs.config()
config.enable_stream(rs.stream.color, 640, 360, rs.format.bgr8, FRAMES_PER_SECOND)
config.enable_stream(rs.stream.depth, 640, 360, rs.format.z16, FRAMES_PER_SECOND)

# ストリーミング開始
pipeline = rs.pipeline()
profile = pipeline.start(config)

# Alignオブジェクト生成
align_to = rs.stream.color
align = rs.align(align_to)


class RecorderState(Enum):
    WAITING = auto()
    COUNTING = auto()
    RECORDING = auto()

recorder_state = RecorderState.WAITING
frame_counter = 0

recorded_colors = np.zeros((FRAMES_PER_SECOND*10,360,640,3), dtype=np.uint8)
recorded_depths = np.zeros((FRAMES_PER_SECOND*10,360,640))
time_start = None

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

        if recorder_state == RecorderState.COUNTING:
            count_down = 3 - (frame_counter // FRAMES_PER_SECOND)
            color_image = cv2.putText(
                color_image, f"{int(count_down)}",(50,50),
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
            color_image = cv2.putText(
                color_image, f"REC",(50,50),
                cv2.FONT_HERSHEY_PLAIN, 2, (0,0,200), 3
            )
            if frame_counter == recorded_colors.shape[0]:
                print(f"save: {time.time() - time_start}s")
                date_str = datetime.datetime.now().strftime('%Y-%m-%d-%H-%M-%S')
                np.savez_compressed(
                    f"{date_str}-depth.npz",
                    recorded_depths.astype(np.int16)
                )
                fmt = cv2.VideoWriter_fourcc(*"mp4v")
                writer = cv2.VideoWriter(f"{date_str}-rgb.avi", fmt, 30.0, (640,360))
                for i in range(recorded_colors.shape[0]):
                    writer.write(recorded_colors[i,:,:,:])
                writer.release()
                recorder_state = RecorderState.WAITING
        else:
            color_image = cv2.putText(
                color_image, f"press r",(50,50),
                cv2.FONT_HERSHEY_PLAIN, 2, (0,0,200), 3
            )

        cv2.namedWindow("Recorder", cv2.WINDOW_AUTOSIZE)
        cv2.imshow("Recorder", np.vstack((color_image, depth_colormap)))

        k = cv2.waitKey(1)
        if k & 0xff == 27:
            cv2.destroyAllWindows()
            break
        elif k == ord("r") and recorder_state == RecorderState.WAITING:
            print("count start")
            recorder_state = RecorderState.COUNTING
            frame_counter = 0
        # elif k == ord("s") and recorder_state == RecorderState.RECORDING:
        #     print("stop")
        #     recorder_state = RecorderState.WAITING
        #     frame_counter = 0
finally:
    pipeline.stop()
