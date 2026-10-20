#!/usr/bin/env python3
"""
server.py -- the cursed file-polling inference "server" uwu ;33

loads the model once, then loops forever:
    wait for predict-N.png  ->  find boxes  ->  write result-N.txt  ->  N += 1
N starts at 0 (or --start) and just keeps going up >_< nya~

result-N.txt looks like this (pixel coords of the ORIGINAL image, x1 y1 x2 y2 = top-left then bottom-right corner,
then the confidence from 0 to 1, best box first):
    box 10 20 100 200 0.9132
    box 20 20 140 120 0.4471
    end
no detections -> the file is just the line "end" owo

usage:
    python server.py
    python server.py --dir some_folder --conf 0.3 --weights runs_milk/stage1/weights/best.pt

for the client side: write predict-N.png however you like (half-written is fine, we
wait for it to be complete), then wait for result-N.txt to exist and read until "end" uwu
"""
import argparse
import os
import sys
import time
from pathlib import Path

import cv2
import numpy as np
from ultralytics import YOLO

# every valid png starts with this signature and ends with an IEND chunk,
# so "ends with IEND" == "the writer finished" (no guessing with sleeps) ;33
PNG_SIG = b"\x89PNG\r\n\x1a\n"
PNG_END = b"\x00\x00\x00\x00IEND\xaeB`\x82"

POLL_SECONDS = 0.1  # the 100ms retry >_<


def newest_weights():
    found = list(Path(".").glob("runs*/**/weights/best.pt"))
    if not found:
        raise SystemExit("couldn't find any best.pt, pass --weights yourself >_<")
    return max(found, key=lambda p: p.stat().st_mtime)


def try_load(path):
    """returns (image, None) when ready, or (None, reason) when we should wait nya~"""
    try:
        data = path.read_bytes()
    except OSError:
        # not there yet, or (windows) still locked by whoever is writing it owo
        return None, "not there yet"
    if not data.startswith(PNG_SIG) or not data.endswith(PNG_END):
        return None, "still being written"
    # imdecode instead of imread so weird characters in the path can't bite us uwu
    img = cv2.imdecode(np.frombuffer(data, np.uint8), cv2.IMREAD_COLOR)
    if img is None:
        return None, "complete png but cv2 can't decode it (corrupt?)"
    return img, None


def write_result(path, lines):
    # write to a temp file then rename, rename is atomic, so the client can never
    # see a half-written result-N.txt. the 'end' line is a second safety net ;33
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text("\n".join(lines) + "\n")
    os.replace(tmp, path)


def main():
    # flush every line, otherwise the log stays empty when output is redirected to a file or pipe >_<
    sys.stdout.reconfigure(line_buffering=True)

    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", default=".", help="folder where predict-N.png shows up and result-N.txt goes uwu")
    ap.add_argument("--weights", default=None, help="path to best.pt (default: newest one found)")
    ap.add_argument("--conf", type=float, default=0.25, help="min confidence for a box >_<")
    ap.add_argument("--imgsz", type=int, default=224, help="same size you trained with nya~")
    ap.add_argument("--start", type=int, default=0, help="first integer (default 0) owo")
    args = ap.parse_args()

    d = Path(args.dir)
    d.mkdir(parents=True, exist_ok=True)

    weights = Path(args.weights) if args.weights else newest_weights()
    print(f"loading {weights} uwu")
    model = YOLO(str(weights))

    # first predict() is slow from one-time setup, so do a throwaway one now
    # instead of making the first real request pay for it ;33
    model.predict(np.zeros((args.imgsz, args.imgsz, 3), np.uint8), imgsz=args.imgsz,
                  device="cpu", verbose=False)

    i = args.start
    print(f"ready! waiting for {d / f'predict-{i}.png'} (ctrl+c to stop) nya~")

    last_note = None  # so we don't spam the same waiting message 10 times a second owo
    try:
        while True:
            src = d / f"predict-{i}.png"
            img, why = try_load(src)
            if img is None:
                # silent while the file just doesn't exist yet (that's the idle state),
                # but say something if it's there and stuck >_<
                if why != "not there yet" and last_note != (i, why):
                    print(f"predict-{i}.png: {why}, waiting...")
                    last_note = (i, why)
                time.sleep(POLL_SECONDS)
                continue

            h, w = img.shape[:2]
            t0 = time.perf_counter()
            result = model.predict(img, imgsz=args.imgsz, conf=args.conf, device="cpu", verbose=False)[0]
            ms = (time.perf_counter() - t0) * 1000

            # xyxy is already in the original image's pixel coordinates, ultralytics undoes the resize for us uwu
            lines = []
            for box in result.boxes:
                x1, y1, x2, y2 = (int(round(v)) for v in box.xyxy[0].tolist())
                conf = float(box.conf[0])  # 0.0 - 1.0, higher = more sure uwu
                lines.append(f"box {x1} {y1} {x2} {y2} {conf:.4f}")
            lines.append("end")

            write_result(d / f"result-{i}.txt", lines)
            print(f"predict-{i}.png ({w}x{h}): {len(lines) - 1} box(es), predict {ms:.1f} ms -> result-{i}.txt nya~")
            i += 1
    except KeyboardInterrupt:
        print(f"\nstopped, next one would have been predict-{i}.png. bye bye uwu ;33")


if __name__ == "__main__":
    main()