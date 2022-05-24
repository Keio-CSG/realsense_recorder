import pyrealsense2 as rs
import numpy as np
import cv2
import time
import sys
# ストリーム(Color/Depth/Infrared)の設定

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(2)

    file_name = sys.argv[1]

    config = rs.config()
    # ↓ ここでファイル名設定
    config.enable_device_from_file(f"./data/{file_name}")
    config.enable_stream(rs.stream.color, 640, 360, rs.format.bgr8, 30)
    config.enable_stream(rs.stream.depth, 640, 360, rs.format.z16, 30)

    # ストリーミング開始
    pipeline = rs.pipeline()
    profile = pipeline.start(config)

    align_to = rs.stream.color
    align = rs.align(align_to)

    start = time.time()
    n = 0

    try:
        while True:
            frames = pipeline.wait_for_frames()
            aligned_frames = align.process(frames)
            color_frame = aligned_frames.get_color_frame()
            depth_frame = aligned_frames.get_depth_frame()
            # 再生秒数の表示
            now = time.time()
            if (now - start) > n:
                n += 1

            if not depth_frame or not color_frame:
                continue

            # Convert images to numpy arrays
            depth_image = np.asanyarray(depth_frame.get_data())
            color_image = np.asanyarray(color_frame.get_data())

            # depth imageをカラーマップに変換
            depth_colormap = cv2.applyColorMap(cv2.convertScaleAbs(
                depth_image, alpha=0.08), cv2.COLORMAP_JET)
            # Show images
            images = np.vstack((color_image, depth_colormap))
            cv2.putText(images,
                        'Exit: "Esc"',
                        (515, 25),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.7,
                        (0, 255, 0),
                        2,
                        cv2.LINE_4)
            cv2.imshow('color_image', images)

            k = cv2.waitKey(1)
            if k & 0xff == 27:  # ESCで終了
                cv2.destroyAllWindows()
                break

    finally:

        # Stop streaming
        pipeline.stop()
