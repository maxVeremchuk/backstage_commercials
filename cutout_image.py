import cv2

# Load video (add file extension)
video = cv2.VideoCapture("hs_video.mp4")

# Check if video opened successfully
if not video.isOpened():
    print("Error: Could not open video file. Make sure 'hs_video.mp4' exists.")
    exit()

# Set frame position to frame 10
video.set(cv2.CAP_PROP_POS_FRAMES, 78)

# Read the frame
success, frame = video.read()

if success:
    # Save frame as PNG
    cv2.imwrite("first_hs.png", frame)
    print("Frame 10 saved as first_hs.png")
else:
    print("Failed to read frame 10")

# Release video
video.release()