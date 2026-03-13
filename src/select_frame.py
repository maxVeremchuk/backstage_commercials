import os
import cv2
import json
import base64
import numpy as np
from typing import List, Dict, Any, Tuple, Optional
from openai import OpenAI

import dotenv
dotenv.load_dotenv()

def find_best_product_placement_shot(
    video_path: str,
    min_shot_sec: float = 1.0,
    max_shot_sec: float = 5.0,
    resize_width: int = 640,
    max_llm_shots: int = 3,
    sample_frames_per_shot: int = 4,
) -> Dict[str, Any]:
    """
    Detect cuts, evaluate each shot for stable background, and ask the LLM
    whether the shot is suitable for product placement.

    Rules:
    - ignore shots shorter than 1 sec
    - ignore shots longer than 5 sec
    - people moving is acceptable
    - background/camera instability is not acceptable
    - send several representative frames from the shot to the LLM

    Returns:
    {
        "best_shot_start_frame": int,
        "best_shot_end_frame": int,
        "best_center_frame": int,
        "fps": float,
        "duration_sec": float,
        "score": float,
        "explanations": [...],
        "llm_analysis": {...}
    }
    """

    client = OpenAI(
        api_key=os.getenv("NOVA_API_KEY"),
        base_url="https://api.nova.amazon.com/v1"
    )

    # ============================================================
    # Helpers
    # ============================================================
    def resize_keep_aspect(img: np.ndarray, width: int) -> np.ndarray:
        h, w = img.shape[:2]
        if w <= width:
            return img
        nh = int(h * width / w)
        return cv2.resize(img, (width, nh), interpolation=cv2.INTER_AREA)

    def to_gray(img: np.ndarray) -> np.ndarray:
        return cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    def encode_b64_jpg(img: np.ndarray) -> str:
        ok, buf = cv2.imencode(".jpg", img, [int(cv2.IMWRITE_JPEG_QUALITY), 85])
        if not ok:
            raise RuntimeError("Failed to encode image")
        return base64.b64encode(buf.tobytes()).decode("utf-8")

    def hist_diff(img1: np.ndarray, img2: np.ndarray) -> float:
        h1 = cv2.calcHist([img1], [0, 1, 2], None, [8, 8, 8], [0, 256, 0, 256, 0, 256])
        h2 = cv2.calcHist([img2], [0, 1, 2], None, [8, 8, 8], [0, 256, 0, 256, 0, 256])
        cv2.normalize(h1, h1)
        cv2.normalize(h2, h2)
        sim = cv2.compareHist(h1, h2, cv2.HISTCMP_CORREL)
        sim = max(min(sim, 1.0), -1.0)
        return 1.0 - ((sim + 1.0) / 2.0)  # convert similarity to difference

    def mean_abs_diff(g1: np.ndarray, g2: np.ndarray) -> float:
        return float(np.mean(np.abs(g1.astype(np.float32) - g2.astype(np.float32))))

    def detect_shot_boundaries(frames: List[np.ndarray]) -> List[int]:
        """
        Return list of start indices of shots. Includes 0 and len(frames).
        Uses a mix of histogram diff and gray diff, with adaptive threshold.
        """
        if len(frames) < 2:
            return [0, len(frames)]

        diffs = []
        for i in range(1, len(frames)):
            f_prev = frames[i - 1]
            f_cur = frames[i]
            g_prev = to_gray(f_prev)
            g_cur = to_gray(f_cur)

            hd = hist_diff(f_prev, f_cur)
            gd = min(mean_abs_diff(g_prev, g_cur) / 60.0, 1.0)
            score = 0.6 * hd + 0.4 * gd
            diffs.append(score)

        arr = np.array(diffs, dtype=np.float32)
        mu = float(arr.mean())
        sigma = float(arr.std() + 1e-6)

        # adaptive cut threshold
        thr = mu + 2.5 * sigma
        thr = max(thr, 0.28)

        shot_starts = [0]
        for i, score in enumerate(diffs, start=1):
            if score >= thr:
                shot_starts.append(i)

        if shot_starts[-1] != len(frames):
            shot_starts.append(len(frames))

        # remove duplicates just in case
        shot_starts = sorted(set(shot_starts))
        if shot_starts[0] != 0:
            shot_starts = [0] + shot_starts
        if shot_starts[-1] != len(frames):
            shot_starts.append(len(frames))

        return shot_starts

    def sample_indices_in_shot(start: int, end: int, k: int) -> List[int]:
        """
        Sample k representative frames inside [start, end].
        """
        if end < start:
            return []
        length = end - start + 1
        if length <= k:
            return list(range(start, end + 1))
        vals = np.linspace(start, end, num=k, dtype=int)
        return vals.tolist()

    def estimate_background_change_in_shot(frames: List[np.ndarray], indices: List[int]) -> Dict[str, float]:
        """
        Estimate whether the background is stable across sampled frames.

        Idea:
        - Try to align consecutive frames using feature matching + homography.
        - After alignment, compute residual difference.
        - Large local motion but small aligned residual means moving people only.
        - Large aligned residual means background/camera change.
        """
        if len(indices) < 2:
            return {
                "background_change": 1.0,
                "foreground_motion": 1.0,
                "camera_instability": 1.0,
                "bg_stability_score": 0.0,
                "homography_success_rate": 0.0,
            }

        orb = cv2.ORB_create(1200)
        bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)

        bg_changes = []
        fg_motions = []
        cam_instabilities = []
        successes = 0

        for a, b in zip(indices[:-1], indices[1:]):
            img1 = frames[a]
            img2 = frames[b]
            g1 = to_gray(img1)
            g2 = to_gray(img2)

            kp1, des1 = orb.detectAndCompute(g1, None)
            kp2, des2 = orb.detectAndCompute(g2, None)

            if des1 is None or des2 is None or len(kp1) < 8 or len(kp2) < 8:
                # fallback: treat as unstable
                raw = min(mean_abs_diff(g1, g2) / 50.0, 1.0)
                bg_changes.append(raw)
                fg_motions.append(raw)
                cam_instabilities.append(1.0)
                continue

            matches = bf.match(des1, des2)
            matches = sorted(matches, key=lambda x: x.distance)

            if len(matches) < 12:
                raw = min(mean_abs_diff(g1, g2) / 50.0, 1.0)
                bg_changes.append(raw)
                fg_motions.append(raw)
                cam_instabilities.append(1.0)
                continue

            pts1 = np.float32([kp1[m.queryIdx].pt for m in matches[:150]]).reshape(-1, 1, 2)
            pts2 = np.float32([kp2[m.trainIdx].pt for m in matches[:150]]).reshape(-1, 1, 2)

            H, mask = cv2.findHomography(pts2, pts1, cv2.RANSAC, 4.0)
            if H is None:
                raw = min(mean_abs_diff(g1, g2) / 50.0, 1.0)
                bg_changes.append(raw)
                fg_motions.append(raw)
                cam_instabilities.append(1.0)
                continue

            successes += 1
            warped2 = cv2.warpPerspective(img2, H, (img1.shape[1], img1.shape[0]))
            gw2 = to_gray(warped2)

            # residual after alignment ≈ background inconsistency / large structure change
            residual = cv2.absdiff(g1, gw2)
            residual_blur = cv2.GaussianBlur(residual, (5, 5), 0)

            # threshold moving areas
            _, moving_mask = cv2.threshold(residual_blur, 22, 255, cv2.THRESH_BINARY)
            moving_ratio = float(np.mean(moving_mask > 0))

            # estimate global residual
            bg_change = min(float(np.mean(residual_blur)) / 45.0, 1.0)

            # foreground motion:
            # if moving regions are small/moderate but total frame remains aligned, that is okay
            fg_motion = min(moving_ratio / 0.35, 1.0)

            # camera instability from homography shape deviation
            # if H is near identity, more stable
            Hn = H / (H[2, 2] + 1e-8)
            identity = np.eye(3, dtype=np.float32)
            cam_inst = min(float(np.mean(np.abs(Hn - identity))) / 0.12, 1.0)

            bg_changes.append(bg_change)
            fg_motions.append(fg_motion)
            cam_instabilities.append(cam_inst)

        background_change = float(np.mean(bg_changes))
        foreground_motion = float(np.mean(fg_motions))
        camera_instability = float(np.mean(cam_instabilities))
        homography_success_rate = successes / max(len(indices) - 1, 1)

        # people motion is okay, background/camera change is not
        bg_stability_score = (
            0.65 * (1.0 - background_change) +
            0.20 * (1.0 - camera_instability) +
            0.15 * (foreground_motion)   # allows some motion, means scene is alive
        )
        bg_stability_score = float(max(0.0, min(bg_stability_score, 1.0)))

        return {
            "background_change": background_change,
            "foreground_motion": foreground_motion,
            "camera_instability": camera_instability,
            "bg_stability_score": bg_stability_score,
            "homography_success_rate": homography_success_rate,
        }

    def build_contact_sheet(frames_list: List[np.ndarray], labels: List[str]) -> np.ndarray:
        target_h = 220
        rendered = []
        for img, label in zip(frames_list, labels):
            h, w = img.shape[:2]
            nw = int(w * target_h / h)
            r = cv2.resize(img, (nw, target_h), interpolation=cv2.INTER_AREA)
            cv2.putText(
                r, label, (10, 24),
                cv2.FONT_HERSHEY_SIMPLEX, 0.75, (0, 255, 0), 2, cv2.LINE_AA
            )
            rendered.append(r)
        return cv2.hconcat(rendered)

    def ask_llm_about_shot(
        sampled_frames: List[np.ndarray],
        sampled_indices: List[int],
        shot_start: int,
        shot_end: int
    ) -> Dict[str, Any]:
        """
        Ask the LLM if the shot is suitable for product placement.
        """
        sheet = build_contact_sheet(
            sampled_frames,
            [f"f{idx}" for idx in sampled_indices]
        )
        sheet = resize_keep_aspect(sheet, 1600)
        b64 = encode_b64_jpg(sheet)
        mime = "image/jpeg"

        prompt = """
You are evaluating a short continuous video shot for possible product placement.

You will see several frames sampled across time from the SAME shot.

Your task is to determine whether there is a good place in the BACKGROUND where a product can be inserted naturally and consistently across the shot.

Focus on finding stable empty areas in the background, especially:
- shelves
- tables
- counters
- desks
- cabinets
- ledges
- other flat or visually stable support surfaces

Main priority:
- Prefer placement in the BACKGROUND rather than foreground.
- Prefer clearly visible empty space on a stable surface.
- Prefer spots where the inserted product would look natural, believable, and remain consistent through the full shot.

Important evaluation rules:
- People moving is acceptable, as long as the background placement area remains stable and visible.
- Background or support surface should stay visually stable across the sampled frames.
- Camera motion should be small enough that the inserted product would still look believable.
- Do NOT prefer foreground placements unless there is no good background option.
- A good shot should contain a persistent empty region in the background where a product could realistically sit.
- The best candidates are shelves, tables, counters, or similar flat background surfaces with enough visible free space.
- Reject shots where the candidate area is heavily occluded, unstable, too small, or changes too much over time.
- Reject shots where a scene cut or large background change appears inside the shot.

Confidence guidance:
- Set placement_confidence HIGH only when there is a clearly visible, stable, empty, believable background placement area.
- The better, larger, clearer, and more stable the background spot is, the higher the confidence should be.
- If only weak, partial, or uncertain placement areas exist, confidence should be low.
- If no good background placement area exists, confidence should be very low.

Return ONLY valid JSON in exactly this schema:
{
  "good_for_product_placement": true,
  "placement_confidence": 0.0,
  "has_stable_surface": true,
  "background_consistent": true,
  "people_motion_only": true,
  "free_space": 0.0,
  "suggested_region_description": "short text",
  "reasoning_short": "short explanation"
}

Field guidance:
- good_for_product_placement: true only if there is a genuinely usable background placement spot
- placement_confidence: number from 0 to 1, where higher means a stronger and more reliable placement opportunity
- has_stable_surface: true if there is a stable shelf/table/counter-like or otherwise believable support region
- background_consistent: true if the placement area stays visually consistent across frames
- people_motion_only: true if motion is mostly from people/foreground activity rather than background change
- free_space: number from 0 to 1 representing how much usable empty space exists in the candidate placement area
- suggested_region_description: briefly describe the best background placement location
- reasoning_short: brief explanation focused on background suitability, stability, and empty space

""".strip()

        user_message = (
            f"These are frames sampled from one continuous shot, from frame {shot_start} to frame {shot_end}. "
            f"Determine if this shot is good for product placement."
        )

        response = client.chat.completions.create(
            model="nova-2-lite-v1",
            temperature=0,
            response_format={"type": "json_object"},
            messages=[
                {
                    "role": "system",
                    "content": prompt
                },
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": user_message},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:{mime};base64,{b64}"
                            }
                        }
                    ]
                }
            ],
            max_tokens=700
        )

        text = response.choices[0].message.content.replace("```json", "").replace("```", "")
        try:
            return json.loads(text)
        except Exception:
            return {
                "good_for_product_placement": False,
                "placement_confidence": 0.0,
                "has_stable_surface": False,
                "background_consistent": False,
                "people_motion_only": False,
                "free_space": 0.0,
                "suggested_region_description": "",
                "reasoning_short": f"Failed to parse LLM JSON: {text[:200]}"
            }

    # ============================================================
    # Read video
    # ============================================================
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise ValueError(f"Cannot open video: {video_path}")

    fps = float(cap.get(cv2.CAP_PROP_FPS))
    if fps <= 1e-6:
        fps = 30.0

    frames: List[np.ndarray] = []
    while True:
        ok, frame = cap.read()
        if not ok:
            break
        frames.append(resize_keep_aspect(frame, resize_width))
    cap.release()

    if len(frames) < 3:
        raise ValueError("Video is too short")

    # ============================================================
    # 1. Detect cuts / shots
    # ============================================================
    shot_boundaries = detect_shot_boundaries(frames)

    shots: List[Tuple[int, int]] = []
    for s, e in zip(shot_boundaries[:-1], shot_boundaries[1:]):
        print(s, e)
        # treat shot as [s, e-1]
        if e - s <= 0:
            continue
        shots.append((s, e - 1))

    if not shots:
        return {
            "best_shot_start_frame": None,
            "best_shot_end_frame": None,
            "best_center_frame": None,
            "fps": fps,
            "duration_sec": None,
            "score": 0.0,
            "explanations": ["No shots detected."],
            "llm_analysis": None
        }

    # ============================================================
    # 2. Filter by shot length
    # ============================================================
    valid_shots = []
    for start, end in shots:
        duration_sec = (end - start + 1) / fps
        if duration_sec < min_shot_sec:
            continue
        if duration_sec > max_shot_sec:
            continue

        valid_shots.append((start, end, duration_sec))

    if not valid_shots:
        return {
            "best_shot_start_frame": None,
            "best_shot_end_frame": None,
            "best_center_frame": None,
            "fps": fps,
            "duration_sec": None,
            "score": 0.0,
            "explanations": [
                f"No valid shots in the allowed duration range [{min_shot_sec}, {max_shot_sec}] sec."
            ],
            "llm_analysis": None
        }

    # ============================================================
    # 3. CV background evaluation for each valid shot
    # ============================================================
    scored_shots = []
    for start, end, duration_sec in valid_shots:
        sampled_idx = sample_indices_in_shot(start, end, sample_frames_per_shot)
        sampled_frames = [frames[i] for i in sampled_idx]
        print(sampled_idx)

        bg_stats = estimate_background_change_in_shot(frames, sampled_idx)
        print(bg_stats["bg_stability_score"], bg_stats["background_change"], bg_stats["homography_success_rate"])

        # Prefer:
        # - low background change
        # - low camera instability
        # - enough homography success
        cv_score = (
            0.55 * bg_stats["bg_stability_score"] +
            0.25 * (1.0 - bg_stats["background_change"]) +
            0.20 * bg_stats["homography_success_rate"]
        )
        cv_score = float(max(0.0, min(cv_score, 1.0)))

        scored_shots.append({
            "start": start,
            "end": end,
            "duration_sec": duration_sec,
            "sampled_idx": sampled_idx,
            "bg_stats": bg_stats,
            "cv_score": cv_score,
        })

    scored_shots.sort(key=lambda x: x["cv_score"], reverse=True)
    scored_shots = scored_shots[:max_llm_shots]

    # ============================================================
    # 4. Ask LLM on best CV candidate shots
    # ============================================================
    enriched = []
    for shot in scored_shots:
        sampled_frames = [frames[i] for i in shot["sampled_idx"]]
        llm = ask_llm_about_shot(
            sampled_frames=sampled_frames,
            sampled_indices=shot["sampled_idx"],
            shot_start=shot["start"],
            shot_end=shot["end"]
        )

        conf = float(llm.get("placement_confidence", 0.0))
        free_space = float(llm.get("free_space", 0.0))
        good = bool(llm.get("good_for_product_placement", False))
        stable_surface = bool(llm.get("has_stable_surface", False))
        bg_consistent = bool(llm.get("background_consistent", False))
        people_motion_only = bool(llm.get("people_motion_only", False))

        llm_score = 0.0
        llm_score += 0.40 * conf
        llm_score += 0.20 * free_space
        llm_score += 0.15 if good else 0.0
        llm_score += 0.10 if stable_surface else 0.0
        llm_score += 0.10 if bg_consistent else 0.0
        llm_score += 0.05 if people_motion_only else 0.0
        llm_score = float(max(0.0, min(llm_score, 1.0)))

        total_score = llm_score#0.50 * shot["cv_score"] + 0.50 * llm_score

        enriched.append({
            **shot,
            "llm": llm,
            "llm_score": llm_score,
            "total_score": total_score,
        })
        print("--------------------------------")
        print(llm, llm_score)
        print("--------------------------------")

    enriched.sort(key=lambda x: x["total_score"], reverse=True)
    best = enriched[0]

    best_center = (best["start"] + best["end"]) // 2

    explanations = [
        f"Best shot is frames {best['start']} to {best['end']} "
        f"({best['duration_sec']:.2f} sec).",
        f"The shot passed the duration filter: between {min_shot_sec:.1f} sec and {max_shot_sec:.1f} sec.",
        f"Background stability score={best['bg_stats']['bg_stability_score']:.3f}, "
        f"background_change={best['bg_stats']['background_change']:.3f}, "
        f"camera_instability={best['bg_stats']['camera_instability']:.3f}, "
        f"foreground_motion={best['bg_stats']['foreground_motion']:.3f}.",
        f"Sampled frames for LLM: {best['sampled_idx']}.",
        f"LLM reasoning: {best['llm'].get('reasoning_short', 'No explanation returned')}",
    ]
    region_desc = best["llm"].get("suggested_region_description", "")
    if region_desc:
        explanations.append(f"Suggested insertion region: {region_desc}")

    return {
        "best_shot_start_frame": best["start"],
        "best_shot_end_frame": best["end"],
        "best_center_frame": best_center,
        "fps": fps,
        "duration_sec": best["duration_sec"],
        "score": best["total_score"],
        "explanations": explanations,
        "llm_analysis": best["llm"]
    }
    
if __name__ == "__main__":
    
    result = find_best_product_placement_shot(
    video_path="../hs_video.mp4"
    )

    print(json.dumps(result, indent=2))