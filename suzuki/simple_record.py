import pyrealsense2 as rs
import numpy as np
import cv2
import time

# ストリーム(Depth/Color)の設定
config = rs.config()
#config.enable_stream(rs.stream.color, 1280, 720, rs.format.bgr8, 30)
#config.enable_stream(rs.stream.depth, 1280, 720, rs.format.z16, 30)
#
config.enable_stream(rs.stream.color, 640, 360, rs.format.bgr8, 30)
config.enable_stream(rs.stream.depth, 640, 360, rs.format.z16, 30)

recording = False
first_check = True

# ストリーミング開始
pipeline = rs.pipeline()
profile = pipeline.start(config)

# Alignオブジェクト生成
align_to = rs.stream.color
align = rs.align(align_to)
device = profile.get_device()
print(device)

start = time.time()
frame_counter = 0
n = 0


try:
    while True:

        # フレーム待ち(Color & Depth)
        frames = pipeline.wait_for_frames()
        frame_counter += 1
        fps = round(frame_counter / (time.time() - start), 1)

        aligned_frames = align.process(frames)
        color_frame = aligned_frames.get_color_frame()
        depth_frame = aligned_frames.get_depth_frame()
        if not depth_frame or not color_frame:
            continue

        # imageをnumpy arrayに
        color_image = np.asanyarray(color_frame.get_data())
        depth_image = np.asanyarray(depth_frame.get_data())

        # depth imageをカラーマップに変換
        depth_colormap = cv2.applyColorMap(cv2.convertScaleAbs(
            depth_image, alpha=0.08), cv2.COLORMAP_JET)

        # 画像表示
        color_image_s = cv2.resize(color_image, (640, 360))
        depth_colormap_s = cv2.resize(depth_colormap, (640, 360))
        cv2.putText(color_image_s,
                    f"fps: {str(fps)}",
                    (25, 25),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7,
                    (0, 255, 0),
                    2,
                    cv2.LINE_4)

        if recording:
            if first_check:
                print("Recording...")
                recorder = rs.recorder("./data/recorded.bag", device)
                record_start = time.time()
                first_check = False
            now = time.time()
            if (now - record_start) > n+1:
                n += 1
                # print(f"Recording... {str(n)} seconds")

            cv2.putText(color_image_s,
                        "RECORDING_TIME: " +
                        str(n) + " sec",
                        (25, 50),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.7,
                        (0, 255, 0),
                        2,
                        cv2.LINE_4)
            cv2.rectangle(color_image_s, (0, 0), (640, 357),
                          (0, 255, 0), thickness=3)

        images = np.vstack((color_image_s, depth_colormap_s))
        cv2.namedWindow('RealSense', cv2.WINDOW_AUTOSIZE)
        cv2.imshow('RealSense', images)

        if cv2.waitKey(2) & 0xff == 27:  # ESCで終了
            cv2.destroyAllWindows()
            break

        if cv2.waitKey(2) & 0xff == ord("r"):  # Rキーで録画開始
            recording = True


finally:

    # ストリーミング停止
    pipeline.stop()
