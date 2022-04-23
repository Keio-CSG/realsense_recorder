import argparse
import time
import json
import os
import cv2
import numpy as np

from common import DisplayMethod

def replay(color_file: str, depth_file: str, frequency: int, display: DisplayMethod):
    """
    ファイルに保存されていた動画データを再生する
    """
    video = cv2.VideoCapture(color_file)

    depth_frames = np.load(depth_file)
    depth_frames = depth_frames[depth_frames.files[0]]

    frame_count = 0

    past_frame_time = time.time()
    sec_per_frame = 1.0 / frequency

    try:
        while True:
            ret, color_frame = video.read()
            depth_frame = depth_frames[frame_count,:,:]

            depth_colormap = cv2.applyColorMap(
                cv2.convertScaleAbs(depth_frame, alpha=0.08), cv2.COLORMAP_JET
            )

            current_time = time.time()
            time.sleep(max(0, sec_per_frame - (current_time - past_frame_time)))
            past_frame_time = current_time

            cv2.namedWindow("Replay", cv2.WINDOW_AUTOSIZE)
            if display == DisplayMethod.STACK:
                # cv2.imshow("Replay", np.vstack((color_frame, depth_colormap)))
                cv2.imshow("Replay", np.vstack((depth_colormap, color_frame)))
            else:
                img_mask = cv2.bitwise_not(cv2.inRange(depth_colormap, np.array([128,0,0]), np.array([128,0,0])))
                depth_colormap = cv2.bitwise_and(depth_colormap, depth_colormap, mask=img_mask)

                blended = cv2.addWeighted(color_frame, 0.5, depth_colormap, 0.5, 0)
                cv2.imshow("Replay", blended)

            k = cv2.waitKey(1)
            if k & 0xff == 27:
                cv2.destroyAllWindows()
                break

            frame_count += 1
            if frame_count >= depth_frames.shape[0]:
                cv2.destroyAllWindows()
                break
    finally:
        video.release()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("json", help="configuration file path")
    parser.add_argument("-d", "--display", default="stack", choices={"stack", "blend"}, help="display method")
    args = parser.parse_args()
    json_path = args.json
    dir = os.path.split(os.path.abspath(json_path))[0]
    with open(json_path) as f:
        config = json.load(f)
        print(config)

    color_path = os.path.join(dir, config["color_file"])
    depth_path = os.path.join(dir, config["depth_file"])
    frequency = config["frequency"]
    display = DisplayMethod.STACK if args.display == "stack" else DisplayMethod.BLEND

    replay(color_path, depth_path, frequency, display)
