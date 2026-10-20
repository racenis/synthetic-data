#!/usr/bin/env python3
"""
predict.py -- run a trained model on a png/jpg (or a whole folder) and save
copies with the detected boxes drawn on top uwu ;33

usage:
    python predict.py my_photo.png
    python predict.py photos_folder --conf 0.1
    python predict.py my_photo.png --weights runs_milk/stage1/weights/best.pt --out predictions

if you don't pass --weights it grabs the newest best.pt it can find under ./runs* nya~
"""
import argparse
import time
from pathlib import Path

import cv2
from ultralytics import YOLO

EXTS = {".png", ".jpg", ".jpeg", ".bmp", ".webp"}


def newest_weights():
    # look in every runs* folder, newest best.pt wins owo
    found = list(Path(".").glob("runs*/**/weights/best.pt"))
    if not found:
        raise SystemExit("couldn't find any best.pt, pass --weights yourself >_<")
    return max(found, key=lambda p: p.stat().st_mtime)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("source", help="an image file or a folder of images uwu")
    ap.add_argument("--weights", default=None, help="path to best.pt (default: newest one found)")
    ap.add_argument("--out", default="predictions", help="where the drawn copies go >_<")
    ap.add_argument("--conf", type=float, default=0.25, help="min confidence, lower it if nothing shows up nya~")
    ap.add_argument("--imgsz", type=int, default=224, help="use the same size you trained with ;33")
    ap.add_argument("--no-warmup", action="store_true",
                    help="skip the untimed warmup run (first call is usually slower, so we do one first owo)")
    args = ap.parse_args()

    weights = Path(args.weights) if args.weights else newest_weights()
    print(f"using weights: {weights} uwu")
    model = YOLO(str(weights))

    src = Path(args.source)
    if src.is_dir():
        paths = sorted(p for p in src.iterdir() if p.suffix.lower() in EXTS)
    else:
        paths = [src]
    if not paths:
        raise SystemExit("no images found owo")

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    # the very first predict() call has extra one-time setup cost, so we burn one
    # untimed run on the first image to make the real timings honest uwu ;33
    if not args.no_warmup:
        warm = cv2.imread(str(paths[0]), cv2.IMREAD_COLOR)
        if warm is not None:
            model.predict(warm, imgsz=args.imgsz, conf=args.conf, device="cpu", verbose=False)

    total = 0
    times = []   # milliseconds per image, prediction only >_<
    for p in paths:
        img = cv2.imread(str(p), cv2.IMREAD_COLOR)
        if img is None:
            print(f"couldn't read {p} >_<")
            continue

        # boxes come back in the ORIGINAL image's pixel coordinates, ultralytics undoes the resizing for us ;33
        # timer wraps ONLY the predict call: no model loading, no imread, no drawing, no saving nya~
        # (perf_counter is the right clock for this, it's monotonic and high resolution uwu)
        t0 = time.perf_counter()
        result = model.predict(img, imgsz=args.imgsz, conf=args.conf, device="cpu", verbose=False)[0]
        ms = (time.perf_counter() - t0) * 1000
        times.append(ms)

        n = 0
        for box in result.boxes:
            x1, y1, x2, y2 = (int(round(v)) for v in box.xyxy[0].tolist())
            conf = float(box.conf[0])
            name = result.names[int(box.cls[0])]
            cv2.rectangle(img, (x1, y1), (x2, y2), (0, 255, 0), 2)
            ty = y1 - 5 if y1 > 15 else y1 + 15
            cv2.putText(img, f"{name} {conf:.2f}", (x1, ty), cv2.FONT_HERSHEY_SIMPLEX,
                        0.5, (0, 255, 0), 1, cv2.LINE_AA)
            n += 1

        if n == 0:
            cv2.putText(img, "no detections", (5, 18), cv2.FONT_HERSHEY_SIMPLEX,
                        0.6, (0, 0, 255), 1, cv2.LINE_AA)
        cv2.imwrite(str(out / p.name), img)
        total += n
        # ultralytics also reports its own split of that time (resize / network / nms) ;33
        sp = result.speed
        print(f"{p.name}: {n} detection(s), predict took {ms:.1f} ms "
              f"(preprocess {sp['preprocess']:.1f} + inference {sp['inference']:.1f} "
              f"+ postprocess {sp['postprocess']:.1f}) nya~")

    if times:
        print(f"prediction time over {len(times)} image(s): avg {sum(times) / len(times):.1f} ms, "
              f"min {min(times):.1f} ms, max {max(times):.1f} ms uwu")
    print(f"saved copies in: {out.resolve()} uwu ;33")
    if total == 0:
        print("(nothing showing up? try --conf 0.05, an undertrained model is shy >_<)")


if __name__ == "__main__":
    main()