"""
Extracts training/testing frames from handheld smartphone videos every 0.25 seconds.

Expected video naming convention:
  <class_name>__session_XX.mp4
Example:
  shore_temple_vimana__session_01.mp4 -> data/cards/shore_temple_vimana/session_01/frame_0000.jpg
  background__session_02.mp4          -> data/cards/background/session_02/frame_0000.jpg
"""
import argparse
import os
import re
import sys

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DEFAULT_DATA_DIR = os.path.join(REPO_ROOT, "data", "cards")
VIDEO_EXTS = (".mp4", ".mov", ".mkv", ".avi", ".webm")
NAME_PATTERN = re.compile(r"^([a-z0-9_]+)__(session_[a-z0-9_]+)$", re.IGNORECASE)


def extract_video(video_path: str, out_root: str, interval_sec: float = 0.25) -> int:
    import cv2

    base = os.path.splitext(os.path.basename(video_path))[0]
    m = NAME_PATTERN.match(base)
    if not m:
        raise ValueError(
            f"Invalid video filename '{os.path.basename(video_path)}'. Expected format: <class>__session_XX.mp4"
        )

    cls_name = m.group(1).lower()
    session_name = m.group(2).lower()
    out_dir = os.path.join(out_root, cls_name, session_name)
    os.makedirs(out_dir, exist_ok=True)

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise RuntimeError(f"Could not open video file: {video_path}")

    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    frame_idx = 0
    saved_count = 0
    next_capture_ms = 0.0
    step_ms = interval_sec * 1000.0

    while True:
        ret, frame = cap.read()
        if not ret:
            break
        timestamp_ms = (frame_idx / fps) * 1000.0
        if timestamp_ms + 1e-6 >= next_capture_ms:
            out_file = os.path.join(out_dir, f"{session_name}_frame_{saved_count:04d}.jpg")
            cv2.imwrite(out_file, frame, [int(cv2.IMWRITE_JPEG_QUALITY), 95])
            saved_count += 1
            next_capture_ms += step_ms
        frame_idx += 1

    cap.release()
    print(f"[Extract] {os.path.basename(video_path)} -> {saved_count} frames saved to {out_dir}")
    return saved_count


def main():
    parser = argparse.ArgumentParser(description="Extract video frames every 0.25s into data/cards/<class>/session_XX/")
    parser.add_argument("input_path", help="Path to a <class>__session_XX.mp4 file or directory of videos")
    parser.add_argument("--out-dir", default=DEFAULT_DATA_DIR, help="Output root directory (default: data/cards)")
    parser.add_argument("--interval", type=float, default=0.25, help="Sampling interval in seconds (default: 0.25)")
    args = parser.parse_args()

    if not os.path.exists(args.input_path):
        print(f"[Error] Input path not found: {args.input_path}")
        sys.exit(1)

    total = 0
    if os.path.isfile(args.input_path):
        total += extract_video(args.input_path, args.out_dir, args.interval)
    else:
        videos = sorted(
            os.path.join(args.input_path, fn)
            for fn in os.listdir(args.input_path)
            if fn.lower().endswith(VIDEO_EXTS)
        )
        if not videos:
            print(f"[Error] No video files ({VIDEO_EXTS}) found in {args.input_path}")
            sys.exit(1)
        for vp in videos:
            total += extract_video(vp, args.out_dir, args.interval)

    print(f"[Extract] Done! Total extracted frames: {total}")


if __name__ == "__main__":
    main()
