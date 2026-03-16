import cv2
import numpy as np
from ultralytics import YOLO
import subprocess
import os
import shutil
import tempfile


def generate_video(
    filename,
    video_path,
    begin_frame,
    end_frame,
    product_bbox,
    output_path="product_placement.mp4",
    person_expand_px=8,
    feather_px=5,
    conf=0.25,
    # debug / visualization
    show_mask=False,
    mask_opacity=0.35,
    mask_color=(0, 255, 0),
    # artifact control
    recover_original_under_person=1.0,
    recover_blur_ksize=5,
    edge_smooth_px=7,
):
    """
    Generate a video by copying the inserted product region from `filename`
    (an image of the first composited frame) onto subsequent frames from `video_path`,
    while placing segmented people from the original frames in front of the product.

    New options:
        show_mask: overlay detected person mask on output for debugging
        mask_opacity: opacity of debug mask
        mask_color: BGR color of debug mask overlay
        recover_original_under_person:
            1.0 -> fully restore original person pixels over product
            0.0 -> ignore person restoration
            0.6-0.9 often reduces artifacts
        recover_blur_ksize:
            blur original recovered person region a bit before blending
        edge_smooth_px:
            extra smoothing of mask edges to reduce cutout artifacts
    """

    x1, y1, x2, y2 = map(int, product_bbox)

    # -------------------------------------------------
    # Load composited first frame and crop product patch
    # -------------------------------------------------
    composited_img = cv2.imread(filename, cv2.IMREAD_COLOR)
    if composited_img is None:
        raise ValueError(f"Could not read composited frame image: {filename}")

    Hc, Wc = composited_img.shape[:2]
    x1 = max(0, min(x1, Wc - 1))
    x2 = max(0, min(x2, Wc))
    y1 = max(0, min(y1, Hc - 1))
    y2 = max(0, min(y2, Hc))

    if x2 <= x1 or y2 <= y1:
        raise ValueError("Invalid product_bbox after clipping.")

    product_patch = composited_img[y1:y2, x1:x2].copy()

    # -------------------------------------------------
    # Open video
    # -------------------------------------------------
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise ValueError(f"Could not open video: {video_path}")

    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    if fps is None or fps <= 0:
        fps = 30.0

    frame_w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    frame_h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    begin_frame = max(0, int(begin_frame))
    end_frame = min(int(end_frame), total_frames - 1)
    if end_frame < begin_frame:
        raise ValueError("end_frame must be >= begin_frame")

    if x2 > frame_w or y2 > frame_h:
        raise ValueError(
            "product_bbox does not fit inside the video frame size. "
            f"Video size: {(frame_w, frame_h)}, bbox: {product_bbox}"
        )

    # -------------------------------------------------
    # Video writer
    # -------------------------------------------------
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    writer = cv2.VideoWriter(output_path, fourcc, fps, (frame_w, frame_h))
    if not writer.isOpened():
        raise ValueError(f"Could not open video writer for: {output_path}")

    # -------------------------------------------------
    # Load person segmentation model
    # -------------------------------------------------
    # model = YOLO("yolov8x-seg.pt")#.cpu()#YOLO("yolo12l-person-seg-extended.pt")#YOLO("yolov8x-seg.pt")
    PERSON_CLASS_ID = 0  # COCO

    # -------------------------------------------------
    # Helpers
    # -------------------------------------------------
    def get_person_mask(frame):
        """Returns uint8 mask of all people in the frame: 255 where person, 0 elsewhere."""
        # results = model(frame, verbose=False, conf=conf, imgsz=1536)
        person_mask = np.zeros(frame.shape[:2], dtype=np.uint8)

        # if not results:
        return person_mask

        r = results[0]
        if r.masks is None or r.boxes is None:
            return person_mask

        cls = r.boxes.cls
        masks = r.masks.data

        if cls is None or masks is None:
            return person_mask

        cls_np = cls.detach().cpu().numpy().astype(int)
        masks_np = masks.detach().cpu().numpy()

        for i, c in enumerate(cls_np):
            if c != PERSON_CLASS_ID:
                continue
            m = (masks_np[i] > 0.5).astype(np.uint8) * 255
            if m.shape != person_mask.shape:
                m = cv2.resize(
                    m,
                    (person_mask.shape[1], person_mask.shape[0]),
                    interpolation=cv2.INTER_NEAREST,
                )
            person_mask = np.maximum(person_mask, m)

        if person_expand_px > 0:
            k = 2 * person_expand_px + 1
            kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (k, k))
            person_mask = cv2.dilate(person_mask, kernel, iterations=1)

        return person_mask

    def soft_mask(mask, blur_px, extra_smooth_px):
        """
        Convert binary mask to soft alpha in [0,1] with smoother borders.
        """
        m = mask.astype(np.uint8)

        if blur_px > 0:
            k = 2 * blur_px + 1
            m = cv2.GaussianBlur(m, (k, k), 0)

        if extra_smooth_px > 0:
            k2 = 2 * extra_smooth_px + 1
            m = cv2.GaussianBlur(m, (k2, k2), 0)

        return np.clip(m.astype(np.float32) / 255.0, 0.0, 1.0)

    def maybe_blur(img, ksize):
        if ksize is None or ksize <= 1:
            return img
        if ksize % 2 == 0:
            ksize += 1
        return cv2.GaussianBlur(img, (ksize, ksize), 0)

    def overlay_debug_mask(frame, mask, color=(0, 255, 0), opacity=0.35):
        if opacity <= 0:
            return frame
        out = frame.copy()
        color_img = np.zeros_like(frame, dtype=np.uint8)
        color_img[:, :] = color
        mask3 = (mask > 0).astype(np.float32)[..., None]
        out = (
            frame.astype(np.float32) * (1.0 - mask3 * opacity)
            + color_img.astype(np.float32) * (mask3 * opacity)
        )
        return np.clip(out, 0, 255).astype(np.uint8)

    # -------------------------------------------------
    # Process frames
    # -------------------------------------------------
    cap.set(cv2.CAP_PROP_POS_FRAMES, begin_frame)

    for frame_idx in range(begin_frame, end_frame + 1):
        ok, frame = cap.read()
        if not ok:
            break
        print(f"Processing frame {frame_idx}")
        original_frame = frame.copy()

        # Paste product patch
        composed = original_frame.copy()
        composed[y1:y2, x1:x2] = product_patch

        # Segment people on ORIGINAL frame
        person_mask = get_person_mask(original_frame)

        # ROI restriction
        person_mask_roi = person_mask[y1:y2, x1:x2]
        original_roi = original_frame[y1:y2, x1:x2].copy()
        product_roi = composed[y1:y2, x1:x2].copy()

        # Smooth mask to reduce cut artifacts
        alpha = soft_mask(person_mask_roi, feather_px, edge_smooth_px)[..., None]

        # Slightly blur recovered human region to hide segmentation jaggies
        recovered_roi = maybe_blur(original_roi, recover_blur_ksize).astype(np.float32)
        product_roi_f = product_roi.astype(np.float32)

        # Adjustable recovery:
        # alpha=1 means full person region
        # recover_original_under_person controls how strongly original person is restored
        mixed_alpha = np.clip(alpha * recover_original_under_person, 0.0, 1.0)

        blended_roi = (
            mixed_alpha * recovered_roi
            + (1.0 - mixed_alpha) * product_roi_f
        )

        composed[y1:y2, x1:x2] = np.clip(blended_roi, 0, 255).astype(np.uint8)

        # Optional mask visualization on final frame
        if show_mask:
            composed = overlay_debug_mask(
                composed,
                person_mask,
                color=mask_color,
                opacity=mask_opacity,
            )

        writer.write(composed)

    cap.release()
    writer.release()
    return output_path


import os
import cv2
import math
import shutil
import tempfile
import subprocess
import numpy as np


def insert_clip_into_video(
    clip_path,
    original_video_path,
    begin_frame,
    end_frame,
    output_path,
):
    """
    Replace frames [begin_frame, end_frame] in original_video_path with frames from clip_path,
    preserving all original video properties and metadata for web compatibility.

    Pipeline:
    1) Extract segments from original video
    2) Process clip to match original video properties exactly
    3) Concatenate with proper stream handling to avoid frozen frames

    Notes:
    - Preserves original video codec settings where possible
    - Audio is preserved from the original video
    - Final output is browser-friendly MP4 (H.264 + yuv420p + faststart)
    """
    ffmpeg = shutil.which("ffmpeg")
    if ffmpeg is None:
        raise RuntimeError("ffmpeg must be installed and available in PATH")

    original_cap = cv2.VideoCapture(original_video_path)
    if not original_cap.isOpened():
        raise ValueError(f"Could not open original video: {original_video_path}")

    clip_cap = cv2.VideoCapture(clip_path)
    if not clip_cap.isOpened():
        original_cap.release()
        raise ValueError(f"Could not open clip video: {clip_path}")

    try:
        total_frames = int(original_cap.get(cv2.CAP_PROP_FRAME_COUNT))
        fps = float(original_cap.get(cv2.CAP_PROP_FPS))
        width = int(original_cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(original_cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

        if not np.isfinite(fps) or fps <= 0:
            fps = 30.0
        if total_frames <= 0:
            raise ValueError("Original video has no readable frames")
        if width <= 0 or height <= 0:
            raise ValueError(f"Invalid source resolution: {width}x{height}")

        begin_frame = max(0, int(begin_frame))
        end_frame = min(int(end_frame), total_frames - 1)

        if end_frame < begin_frame:
            raise ValueError("end_frame must be >= begin_frame")

        head_end_time = begin_frame / fps
        mid_start_time = begin_frame / fps
        mid_end_time = (end_frame + 1) / fps
        tail_start_time = (end_frame + 1) / fps

        out_dir = os.path.dirname(os.path.abspath(output_path))
        os.makedirs(out_dir, exist_ok=True)

        with tempfile.TemporaryDirectory(prefix="replace_segment_") as tmpdir:
            head_mp4 = os.path.join(tmpdir, "head.mp4")
            middle_mp4 = os.path.join(tmpdir, "middle.mp4")
            tail_mp4 = os.path.join(tmpdir, "tail.mp4")
            concat_list = os.path.join(tmpdir, "concat.txt")

            # 1) Cut HEAD from original without re-encoding if it exists
            if begin_frame > 0:
                cmd = [
                    ffmpeg, "-y",
                    "-i", original_video_path,
                    "-t", f"{head_end_time:.6f}",
                    "-c:v", "libx264",
                    "-preset", "medium",
                    "-crf", "18",
                    "-pix_fmt", "yuv420p",
                    "-c:a", "aac",
                    "-b:a", "192k",
                    "-movflags", "+faststart",
                    head_mp4,
                ]
                subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

            # 2) Process the MIDDLE segment from clip
            # Re-encode to ensure consistent frame rate and timing
            expected_duration = (end_frame - begin_frame + 1) / fps
            
            cmd = [
                ffmpeg, "-y",
                "-i", clip_path,
                "-t", f"{expected_duration:.6f}",
                "-c:v", "libx264",
                "-preset", "medium",
                "-crf", "18",
                "-pix_fmt", "yuv420p",
                "-vf", f"scale={width}:{height},fps={fps}",
                "-vsync", "cfr",  # Constant frame rate
                "-an",  # No audio from clip
                "-movflags", "+faststart",
                middle_mp4,
            ]
            subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

            # 3) Cut TAIL from original without re-encoding if it exists
            if end_frame < total_frames - 1:
                cmd = [
                    ffmpeg, "-y",
                    "-ss", f"{tail_start_time:.6f}",
                    "-i", original_video_path,
                    "-c:v", "libx264",
                    "-preset", "medium",
                    "-crf", "18",
                    "-pix_fmt", "yuv420p",
                    "-c:a", "aac",
                    "-b:a", "192k",
                    "-movflags", "+faststart",
                    tail_mp4,
                ]
                subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

            # 4) Build concat list
            parts = []
            if begin_frame > 0 and os.path.exists(head_mp4) and os.path.getsize(head_mp4) > 0:
                parts.append(head_mp4)
            parts.append(middle_mp4)
            if end_frame < total_frames - 1 and os.path.exists(tail_mp4) and os.path.getsize(tail_mp4) > 0:
                parts.append(tail_mp4)

            with open(concat_list, "w", encoding="utf-8") as f:
                for part in parts:
                    # Fix backslash issue by normalizing path first
                    normalized_path = part.replace('\\', '/')
                    f.write(f"file '{normalized_path}'\n")

            # 5) Concatenate all parts with original audio
            # Use concat demuxer with re-encoding to ensure smooth playback
            temp_video = os.path.join(tmpdir, "temp_video.mp4")
            cmd = [
                ffmpeg, "-y",
                "-f", "concat",
                "-safe", "0",
                "-i", concat_list,
                "-c:v", "libx264",
                "-preset", "medium",
                "-crf", "18",
                "-pix_fmt", "yuv420p",
                "-vsync", "cfr",
                "-movflags", "+faststart",
                temp_video,
            ]
            subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

            # 6) Add audio from original video
            cmd = [
                ffmpeg, "-y",
                "-i", temp_video,
                "-i", original_video_path,
                "-map", "0:v:0",
                "-map", "1:a?",
                "-c:v", "copy",
                "-c:a", "aac",
                "-b:a", "192k",
                "-shortest",
                "-movflags", "+faststart",
                output_path,
            ]
            subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        return output_path

    finally:
        original_cap.release()
        clip_cap.release()
    


if __name__ == "__main__":
    out = generate_video(
    filename="output_bbox_fall2.png",
    video_path="../fallout.mp4",
    begin_frame=100,
    end_frame=400,
    product_bbox=(0, 750, 300, 1150),#(921, 302, 1074, 431),
    output_path="hs_video_with_product_fall.mp4",
    person_expand_px=0,
    feather_px=1,
    edge_smooth_px=1,
    recover_original_under_person=1,
    recover_blur_ksize=1,
    show_mask=False,
    mask_opacity=0.25,
    )
    
    
    # out = insert_clip_into_video(
    # 'hs_video_with_product.mp4',
    # '../hs_video.mp4',
    # 78,
    # 170,
    # 'hs_video_with_product_inserted.mp4',
    # )
    
    # out = insert_clip_into_video(
    # r'C:\stuff_pract\amazon_hack\src\hs_video_with_product.mp4',
    # '../frontend/prime-video-ui/public/suits_old.mp4',
    # 9994,
    # 10085,
    # 'suits_with_product_inserted.mp4',
    # )
    
    print(out)