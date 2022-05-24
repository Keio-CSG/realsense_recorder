import argparse
import time
import json
import os
import cv2
import numpy as np

from common import DisplayMethod

def watch_frames(color_file: str, depth_file: str, frequency: int, display: DisplayMethod):
    """
    動画データをページ送りする
    """
    video = cv2.VideoCapture(color_file)

    depth_frames = np.load(depth_file)
    depth_frames = depth_frames[depth_frames.files[0]]

    current_frame = 0

    color_frame = None

    print(np.linalg.norm(depth_frames[0,:,:] - depth_frames[-1,:,:]))

    color_frames = []

    try:
        while True:
            if color_frame is None:
                if current_frame < len(color_frames):
                    color_frame = color_frames[current_frame]
                else:
                    ret, color_frame = video.read()
                    color_frames.append(color_frame)
            depth_frame = depth_frames[current_frame,:,:]

            depth_colormap = cv2.applyColorMap(
                cv2.convertScaleAbs(depth_frame, alpha=0.08), cv2.COLORMAP_JET
            )
            
            color_frame = cv2.putText(
                color_frame, f"{current_frame+1}/{depth_frames.shape[0]}f",(10,50),
                cv2.FONT_HERSHEY_PLAIN, 2, (0,0,200), 3
            )
            cv2.namedWindow("Watch Frames", cv2.WINDOW_AUTOSIZE)
            if display == DisplayMethod.STACK:
                cv2.imshow("Watch Frames", np.vstack((depth_colormap, color_frame)))
            else:
                img_mask = cv2.bitwise_not(cv2.inRange(depth_colormap, np.array([128,0,0]), np.array([128,0,0])))
                depth_colormap = cv2.bitwise_and(depth_colormap, depth_colormap, mask=img_mask)

                blended = cv2.addWeighted(color_frame, 0.5, depth_colormap, 0.5, 0)
                cv2.imshow("Watch Frames", blended)

            k = cv2.waitKey(1)
            if k & 0xff == 27:
                cv2.destroyAllWindows()
                break
            if k & 0xff == ord("d") and current_frame < depth_frames.shape[0] - 1:
                color_frame = None
                current_frame += 1
                continue
            if k & 0xff == ord("a") and current_frame > 0:
                color_frame = None
                current_frame -= 1
                continue
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

    watch_frames(color_path, depth_path, frequency, display)
