import os
import cv2
import json
import base64
import numpy as np
from typing import List, Dict, Any, Optional
from openai import OpenAI
import dotenv

dotenv.load_dotenv()


def find_best_product_placement_interval(
    video_path: str,
    step: int = 5,
    triplet_gap: int = 2,
    max_llm_candidates: int = 20,
    resize_width: int = 640,
    cut_threshold: float = 0.55,
    motion_threshold: float = 1.5,
    min_interval_len: int = 8,
) -> Dict[str, Any]:
    """
    Analyze a video and return the best frame interval for product placement.

    Strategy
    --------
    1. Read video and sample candidate center frames.
    2. For each candidate center i, build triplet (i-gap, i, i+gap).
    3. Use cheap CV metrics first:
         - frame similarity
         - optical-flow-like motion proxy
         - texture / emptiness proxy
       to shortlist candidates.
    4. For shortlisted candidates, ask the LLM if the place is good for insertion.
    5. Pick the best center frame using combined CV + LLM score.
    6. Expand around the best frame with CV-only scene continuity search:
         - stop at cuts
         - stop when background changes too much
    7. Return frame numbers and reasons.

    Returns
    -------
    dict with:
        {
          "best_center_frame": int,
          "scene_start_frame": int,
          "scene_end_frame": int,
          "triplet_checked": [a, b, c],
          "score": float,
          "explanations": [...],
          "llm_analysis": {...}
        }
    """
    print(os.getenv("NOVA_API_KEY"))
    client = OpenAI(
        api_key=os.getenv("NOVA_API_KEY"),
        base_url="https://api.nova.amazon.com/v1"
    )

    # -----------------------------
    # Helpers
    # -----------------------------
    def encode_image_b64(img_bgr: np.ndarray) -> str:
        ok, buf = cv2.imencode(".jpg", img_bgr, [int(cv2.IMWRITE_JPEG_QUALITY), 85])
        if not ok:
            raise RuntimeError("Failed to encode image")
        return base64.b64encode(buf.tobytes()).decode("utf-8")

    def resize_keep_aspect(img: np.ndarray, width: int) -> np.ndarray:
        h, w = img.shape[:2]
        if w <= width:
            return img
        new_h = int(h * width / w)
        return cv2.resize(img, (width, new_h), interpolation=cv2.INTER_AREA)

    def to_gray(img: np.ndarray) -> np.ndarray:
        return cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    def hist_similarity(img1: np.ndarray, img2: np.ndarray) -> float:
        """
        Histogram correlation in [roughly -1, 1], larger is more similar.
        """
        h1 = cv2.calcHist([img1], [0, 1, 2], None, [8, 8, 8], [0, 256, 0, 256, 0, 256])
        h2 = cv2.calcHist([img2], [0, 1, 2], None, [8, 8, 8], [0, 256, 0, 256, 0, 256])
        cv2.normalize(h1, h1)
        cv2.normalize(h2, h2)
        return float(cv2.compareHist(h1, h2, cv2.HISTCMP_CORREL))

    def mean_abs_diff(img1_gray: np.ndarray, img2_gray: np.ndarray) -> float:
        return float(np.mean(np.abs(img1_gray.astype(np.float32) - img2_gray.astype(np.float32))))

    def corner_density(img_gray: np.ndarray) -> float:
        """
        Surface with some texture is better than a blank or highly chaotic frame.
        """
        corners = cv2.goodFeaturesToTrack(img_gray, maxCorners=300, qualityLevel=0.01, minDistance=8)
        n = 0 if corners is None else len(corners)
        area = img_gray.shape[0] * img_gray.shape[1]
        return float(n / max(area, 1) * 1e5)

    def motion_score(img1_gray: np.ndarray, img2_gray: np.ndarray) -> float:
        """
        Cheap motion proxy: mean abs diff after blur.
        Smaller = more stable.
        """
        g1 = cv2.GaussianBlur(img1_gray, (5, 5), 0)
        g2 = cv2.GaussianBlur(img2_gray, (5, 5), 0)
        return mean_abs_diff(g1, g2)

    def build_contact_sheet(frames_triplet: List[np.ndarray], labels: List[str]) -> np.ndarray:
        resized = []
        target_h = 220
        for img, label in zip(frames_triplet, labels):
            h, w = img.shape[:2]
            new_w = int(w * target_h / h)
            r = cv2.resize(img, (new_w, target_h), interpolation=cv2.INTER_AREA)
            cv2.putText(
                r, label, (12, 24), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2, cv2.LINE_AA
            )
            resized.append(r)
        return cv2.hconcat(resized)

    def ask_llm_about_triplet(frames_triplet: List[np.ndarray], triplet_ids: List[int]) -> Dict[str, Any]:
        """
        Ask Nova whether this location is good for product placement.
        The LLM sees 3 frames stitched side-by-side.
        """
        sheet = build_contact_sheet(
            frames_triplet,
            [f"frame {triplet_ids[0]}", f"frame {triplet_ids[1]}", f"frame {triplet_ids[2]}"]
        )
        sheet = resize_keep_aspect(sheet, 1400)
        b64 = encode_image_b64(sheet)
        mime = "image/jpeg"

        prompt = """
You are evaluating whether a video scene is a good candidate for inserting a product placement.

You are shown 3 frames from the same local moment in a video:
left = earlier frame
middle = candidate frame
right = later frame

Decide if the middle frame is a good place for product placement.

Look for:
1. Stable visible surface / region where an object or ad could be placed
2. Background consistency across the 3 frames
3. Low camera/object motion near the candidate region
4. No obvious scene cut between the 3 frames
5. Enough free space / non-occluded area
6. The surface should not deform strongly across frames

Return ONLY valid JSON with this schema:
{
  "good_for_product_placement": true,
  "placement_confidence": 0.0,
  "has_stable_surface": true,
  "background_consistent": true,
  "has_scene_cut": false,
  "free_space": 0.0,
  "suggested_region_description": "short text",
  "reasoning_short": "short explanation"
}

Notes:
- placement_confidence is in [0,1]
- free_space is in [0,1]
- If there is a cut or major change, confidence should be low.
- Output JSON only.
""".strip()

        user_message = (
            f"Triplet frames are {triplet_ids}. "
            f"Judge whether the middle frame {triplet_ids[1]} is a good spot for stable product placement."
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
            max_tokens=600
        )

        content = response.choices[0].message.content
        try:
            return json.loads(content)
        except Exception:
            return {
                "good_for_product_placement": False,
                "placement_confidence": 0.0,
                "has_stable_surface": False,
                "background_consistent": False,
                "has_scene_cut": True,
                "free_space": 0.0,
                "suggested_region_description": "",
                "reasoning_short": f"LLM JSON parse failed. Raw: {content[:200]}"
            }

    def scene_change_score(img_prev: np.ndarray, img_cur: np.ndarray) -> float:
        """
        Higher means more likely a scene cut / large change.
        """
        hsim = hist_similarity(img_prev, img_cur)
        gprev = to_gray(img_prev)
        gcur = to_gray(img_cur)
        mad = mean_abs_diff(gprev, gcur)

        # Normalize roughly
        h_part = 1.0 - max(min((hsim + 1) / 2, 1.0), 0.0)  # convert similarity -> difference
        d_part = min(mad / 60.0, 1.0)

        return 0.6 * h_part + 0.4 * d_part

    def local_stability_score(frames_triplet: List[np.ndarray]) -> Dict[str, float]:
        f0, f1, f2 = frames_triplet
        g0, g1, g2 = map(to_gray, frames_triplet)

        sim01 = hist_similarity(f0, f1)
        sim12 = hist_similarity(f1, f2)
        mot01 = motion_score(g0, g1)
        mot12 = motion_score(g1, g2)
        tex = corner_density(g1)

        # Higher is better
        sim_score = (sim01 + sim12) / 2.0
        motion_penalty = (mot01 + mot12) / 2.0

        # Convert to normalized-ish terms
        sim_norm = max(0.0, min((sim_score + 1.0) / 2.0, 1.0))
        motion_norm = max(0.0, 1.0 - min(motion_penalty / 25.0, 1.0))
        texture_norm = min(tex / 30.0, 1.0)

        # Slight preference for moderate texture
        texture_quality = 1.0 - abs(texture_norm - 0.45)

        score = 0.5 * sim_norm + 0.35 * motion_norm + 0.15 * texture_quality

        return {
            "cv_score": float(score),
            "hist_similarity_avg": float(sim_score),
            "motion_penalty": float(motion_penalty),
            "texture_density": float(tex),
            "scene_change_local": float(max(
                scene_change_score(f0, f1),
                scene_change_score(f1, f2)
            ))
        }

    # -----------------------------
    # Read all frames
    # -----------------------------
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise ValueError(f"Cannot open video: {video_path}")

    frames = []
    idx = 0
    while True:
        ok, frame = cap.read()
        if not ok:
            break
        frames.append(resize_keep_aspect(frame, resize_width))
        idx += 1
    cap.release()

    n = len(frames)
    if n < 2 * triplet_gap + 1:
        raise ValueError("Video too short for triplet analysis")

    # -----------------------------
    # Step 1: CV prefilter
    # -----------------------------
    candidates = []
    for center in range(triplet_gap, n - triplet_gap, step):
        triplet_idx = [center - triplet_gap, center, center + triplet_gap]
        triplet = [frames[triplet_idx[0]], frames[triplet_idx[1]], frames[triplet_idx[2]]]
        cv_stats = local_stability_score(triplet)

        # Keep only reasonably stable local triplets
        if cv_stats["scene_change_local"] < cut_threshold and cv_stats["motion_penalty"] < 20:
            candidates.append({
                "center": center,
                "triplet_idx": triplet_idx,
                "cv_stats": cv_stats
            })

    if not candidates:
        return {
            "best_center_frame": None,
            "scene_start_frame": None,
            "scene_end_frame": None,
            "triplet_checked": None,
            "score": 0.0,
            "explanations": ["No stable candidate triplets found by CV prefilter."],
            "llm_analysis": None
        }

    # Sort by CV quality and keep top few for LLM
    candidates = sorted(candidates, key=lambda x: x["cv_stats"]["cv_score"], reverse=True)
    candidates = candidates[:max_llm_candidates]

    # -----------------------------
    # Step 2: LLM on shortlisted candidates
    # -----------------------------
    enriched = []
    for cand in candidates:
        print("Checking candidate:", cand["center"])
        ids = cand["triplet_idx"]
        triplet = [frames[ids[0]], frames[ids[1]], frames[ids[2]]]

        llm = ask_llm_about_triplet(triplet, ids)

        llm_conf = float(llm.get("placement_confidence", 0.0))
        free_space = float(llm.get("free_space", 0.0))
        good = bool(llm.get("good_for_product_placement", False))
        stable_surface = bool(llm.get("has_stable_surface", False))
        bg_consistent = bool(llm.get("background_consistent", False))
        has_cut = bool(llm.get("has_scene_cut", True))

        llm_score = 0.0
        llm_score += 0.45 * llm_conf
        llm_score += 0.20 * free_space
        llm_score += 0.15 if good else 0.0
        llm_score += 0.10 if stable_surface else 0.0
        llm_score += 0.10 if bg_consistent else 0.0
        llm_score -= 0.35 if has_cut else 0.0
        llm_score = max(llm_score, 0.0)

        total_score = 0.45 * cand["cv_stats"]["cv_score"] + 0.55 * llm_score

        enriched.append({
            **cand,
            "llm": llm,
            "llm_score": float(llm_score),
            "total_score": float(total_score)
        })

    enriched = sorted(enriched, key=lambda x: x["total_score"], reverse=True)
    best = enriched[0]

    best_center = best["center"]

    # -----------------------------
    # Step 3: Expand interval with CV only
    # -----------------------------
    def expand_left(center_idx: int) -> int:
        start = center_idx
        for i in range(center_idx, 0, -1):
            change = scene_change_score(frames[i - 1], frames[i])
            gprev = to_gray(frames[i - 1])
            gcur = to_gray(frames[i])
            mot = motion_score(gprev, gcur)

            if change > cut_threshold or mot > 25:
                break
            start = i - 1
        return start

    def expand_right(center_idx: int) -> int:
        end = center_idx
        for i in range(center_idx, n - 1):
            change = scene_change_score(frames[i], frames[i + 1])
            g1 = to_gray(frames[i])
            g2 = to_gray(frames[i + 1])
            mot = motion_score(g1, g2)

            if change > cut_threshold or mot > 25:
                break
            end = i + 1
        return end

    left = expand_left(best_center)
    right = expand_right(best_center)

    # If too short, keep local triplet at minimum
    if right - left + 1 < min_interval_len:
        left = max(0, best_center - triplet_gap)
        right = min(n - 1, best_center + triplet_gap)

    # -----------------------------
    # Step 4: Build explanations
    # -----------------------------
    explanations = []

    explanations.append(
        f"Best center frame is {best_center} because it had the strongest combined CV+LLM score "
        f"({best['total_score']:.3f})."
    )

    explanations.append(
        f"Triplet checked: {best['triplet_idx']}. "
        f"Local visual stability score={best['cv_stats']['cv_score']:.3f}, "
        f"avg histogram similarity={best['cv_stats']['hist_similarity_avg']:.3f}, "
        f"motion penalty={best['cv_stats']['motion_penalty']:.3f}."
    )

    explanations.append(
        f"LLM judged placement confidence={best['llm_score']:.3f}. "
        f"Reason: {best['llm'].get('reasoning_short', 'No reason returned')}."
    )

    explanations.append(
        f"Continuous scene interval estimated from frame {left} to {right} "
        f"using cut detection and frame-to-frame stability only."
    )

    region_desc = best["llm"].get("suggested_region_description", "")
    if region_desc:
        explanations.append(f"Suggested placement region: {region_desc}")

    return {
        "best_center_frame": best_center,
        "scene_start_frame": left,
        "scene_end_frame": right,
        "triplet_checked": best["triplet_idx"],
        "score": best["total_score"],
        "explanations": explanations,
        "llm_analysis": best["llm"]
    }
    
if __name__ == "__main__":
    
    result = find_best_product_placement_interval(
    video_path="hs_video.mp4",
    step=5,
    triplet_gap=2
    )

    print(json.dumps(result, indent=2))