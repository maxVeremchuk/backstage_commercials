# import cv2
# import numpy as np
# import mediapipe as mp
# # from ultralytics import YOLO
# import matplotlib.pyplot as plt


# # -------------------------------
# # Load image
# # -------------------------------

# image_path = "hs.png"
# img = cv2.imread(image_path)
# img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

# h, w = img.shape[:2]


# # ===============================
# # 1️⃣ MediaPipe Human Segmentation
# # ===============================

# mp_seg = mp.solutions.selfie_segmentation

# with mp_seg.SelfieSegmentation(model_selection=1) as segmenter:

#     result = segmenter.process(img_rgb)

#     mask = result.segmentation_mask

#     human_mask = mask > 0.5

#     human_overlay = img.copy()

#     human_overlay[human_mask] = [0,255,0]  # green mask
    
    
# plt.figure(figsize=(15,5))

# plt.subplot(1,3,1)
# plt.title("Original")
# plt.imshow(img_rgb)
# plt.axis("off")

# plt.subplot(1,3,2)
# plt.title("MediaPipe Human Mask")
# plt.imshow(cv2.cvtColor(human_overlay, cv2.COLOR_BGR2RGB))
# plt.axis("off")

# # plt.subplot(1,3,3)
# # plt.title("YOLO Object Masks")
# # plt.imshow(cv2.cvtColor(yolo_overlay, cv2.COLOR_BGR2RGB))
# # plt.axis("off")

# plt.show()


import cv2
import numpy as np
from ultralytics import YOLO
import matplotlib.pyplot as plt


# -------------------------------
# Load image
# -------------------------------

image_path = "hs.png"
img = cv2.imread(image_path)
img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

h, w = img.shape[:2]



# ===============================
# 2️⃣ YOLOv8 Object Segmentation
# ===============================

model = YOLO("yolov8x-seg.pt")

results = model(img)

yolo_overlay = img.copy()

if results[0].masks is not None:

    masks = results[0].masks.data.cpu().numpy()

    for mask in masks:

        mask = cv2.resize(mask, (w,h))

        colored = np.zeros_like(img)

        colored[:,:,0] = 255  # blue

        yolo_overlay[mask > 0.1] = colored[mask > 0.1]


# ===============================
# 3️⃣ Visualization
# ===============================

plt.figure(figsize=(15,5))

plt.subplot(1,2,1)
plt.title("Original")
plt.imshow(img_rgb)
plt.axis("off")

# plt.subplot(1,3,2)
# plt.title("MediaPipe Human Mask")
# plt.imshow(cv2.cvtColor(human_overlay, cv2.COLOR_BGR2RGB))
# plt.axis("off")

plt.subplot(1,2,2)
plt.title("YOLO Object Masks")
plt.imshow(cv2.cvtColor(yolo_overlay, cv2.COLOR_BGR2RGB))
plt.axis("off")

plt.show()