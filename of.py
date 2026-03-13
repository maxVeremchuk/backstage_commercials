import cv2
import numpy as np

# -----------------------------
# Load video
# -----------------------------
video_path = "hs.webm"
cap = cv2.VideoCapture(video_path)

ret, prev_frame = cap.read()
if not ret:
    raise Exception("Cannot read video")

prev_gray = cv2.cvtColor(prev_frame, cv2.COLOR_BGR2GRAY)

while True:

    ret, frame = cap.read()
    if not ret:
        break

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    # ---------------------------------
    # Compute dense optical flow
    # ---------------------------------
    flow = cv2.calcOpticalFlowFarneback(
        prev_gray,
        gray,
        None,
        pyr_scale=0.5,
        levels=3,
        winsize=15,
        iterations=3,
        poly_n=5,
        poly_sigma=1.2,
        flags=0
    )

    # ---------------------------------
    # Motion magnitude
    # ---------------------------------
    mag, ang = cv2.cartToPolar(flow[...,0], flow[...,1])

    motion_mask = mag > 2.0
    motion_mask = motion_mask.astype(np.uint8) * 255

    # ---------------------------------
    # Clean mask
    # ---------------------------------
    kernel = np.ones((5,5), np.uint8)
    motion_mask = cv2.morphologyEx(motion_mask, cv2.MORPH_OPEN, kernel)
    motion_mask = cv2.dilate(motion_mask, kernel, iterations=2)

    # ---------------------------------
    # Find moving contours
    # ---------------------------------
    contours, _ = cv2.findContours(
        motion_mask,
        cv2.RETR_EXTERNAL,
        cv2.CHAIN_APPROX_SIMPLE
    )

    overlay = frame.copy()

    for cnt in contours:

        if cv2.contourArea(cnt) < 500:
            continue

        x,y,w,h = cv2.boundingRect(cnt)

        cv2.rectangle(overlay,(x,y),(x+w,y+h),(0,255,0),2)

        # draw mask region
        overlay[motion_mask > 0] = [0,0,255]

    # ---------------------------------
    # Show result
    # ---------------------------------
    cv2.imshow("Motion Mask", motion_mask)
    cv2.imshow("Moving Objects", overlay)

    prev_gray = gray

    if cv2.waitKey(1) & 0xFF == 27:
        break

cap.release()
cv2.destroyAllWindows()