import cv2
import numpy as np

LOAD_DATE = "2022-04-20-14-12-35"

video = cv2.VideoCapture(LOAD_DATE + "-rgb.avi")

depth_frames = np.load(LOAD_DATE + "-depth.npz")
depth_frames = depth_frames[depth_frames.files[0]]

frame_count = 0

try:
    while True:
        ret, color_frame = video.read()
        depth_frame = depth_frames[frame_count,:,:]

        depth_colormap = cv2.applyColorMap(
            cv2.convertScaleAbs(depth_frame, alpha=0.08), cv2.COLORMAP_JET
        )

        cv2.namedWindow("Replay", cv2.WINDOW_AUTOSIZE)
        cv2.imshow("Replay", np.vstack((color_frame, depth_colormap)))

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