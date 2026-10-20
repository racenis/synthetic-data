#!/usr/bin/env python3
"""
prep_negatives.py -- turns a folder of REAL photos into negative training images uwu ;33

every photo goes through the same treatment as your synthetic data (orig, flip,
hsv, warp, skew -> random 224 crop), reusing the functions from prep_data.py so
the two can't drift apart >_<. the labels are empty .txt files, which yolo reads
as "nothing to detect here" nya~

IMPORTANT: no milk trucks in these photos!! a milk truck without a box would teach
the model that milk trucks are background owo. other trucks, vans, streets, shops,
fields, indoor stuff etc are all great.

how big photos are handled: each variant gets a random downscale (short side
--min-side..--max-side, never upscaled), then a random --window sized piece (256 =
the size of your synthetic source images) is cut out, then the usual transform +
crop happens on that. so a 4K photo becomes a handful of different "synthetic-sized"
looks instead of one tiny corner >_<

usage (keep this next to prep_data.py):
    python prep_negatives.py my_photos
    python prep_negatives.py my_photos --out . --repeats 3
"""
import argparse
import hashlib
import random
from pathlib import Path

import cv2
import numpy as np

try:
    from prep_data import TRANSFORMS, VARIANTS, random_crop
except ModuleNotFoundError as e:
    if e.name == "prep_data":
        raise SystemExit("can't find prep_data.py, keep this script in the same folder as it >_<")
    raise

EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".webp", ".tif", ".tiff"}


def downscale(img, rng, min_side, max_side):
    """shrink so the short side is a random size in [min_side, max_side], never upscale uwu"""
    h, w = img.shape[:2]
    target = rng.randint(min_side, max_side)
    scale = min(1.0, target / min(h, w))
    if scale == 1.0:
        return img
    size = (round(w * scale), round(h * scale))
    # INTER_AREA is the right one for shrinking, plain bilinear would alias badly on 4K ;33
    return cv2.resize(img, size, interpolation=cv2.INTER_AREA)


def random_window(img, rng, window):
    h, w = img.shape[:2]
    x0 = rng.randint(0, w - window)
    y0 = rng.randint(0, h - window)
    return img[y0:y0 + window, x0:x0 + window]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("src", help="folder with your real photos (no milk trucks!) uwu")
    ap.add_argument("--out", default=".", help="same dataset root you gave prep_data.py >_<")
    ap.add_argument("--crop", type=int, default=224, help="final crop size, same as prep_data.py")
    ap.add_argument("--window", type=int, default=256, help="size of the piece cut before transforms (your synthetic source size) nya~")
    ap.add_argument("--min-side", type=int, default=256, help="smallest random short side after downscaling owo")
    ap.add_argument("--max-side", type=int, default=512, help="largest random short side after downscaling")
    ap.add_argument("--val-frac", type=float, default=0.1, help="fraction of PHOTOS that go to val uwu")
    ap.add_argument("--repeats", type=int, default=1, help="run all 5 variants this many times per photo (each time gets new random scale/crop) ;33")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--recursive", action="store_true", help="also look inside subfolders")
    args = ap.parse_args()

    if args.crop > args.window:
        raise SystemExit("--crop can't be bigger than --window >_<")
    args.min_side = max(args.min_side, args.window)   # so a window always fits, no upscaling needed
    args.max_side = max(args.max_side, args.min_side)

    src, out = Path(args.src), Path(args.out)
    if not src.is_dir():
        raise SystemExit(f"{src} isn't a folder owo")
    files = src.rglob("*") if args.recursive else src.iterdir()
    photos = sorted(p for p in files if p.is_file() and p.suffix.lower() in EXTS)
    if not photos:
        raise SystemExit("no images found in there, nyo~ >_<")

    for split in ("train", "val"):
        (out / "images" / split).mkdir(parents=True, exist_ok=True)
        (out / "labels" / split).mkdir(parents=True, exist_ok=True)

    counts = {"train": 0, "val": 0}
    photos_used = {"train": 0, "val": 0}
    skipped = 0
    for p in photos:
        try:
            data = p.read_bytes()
        except OSError:
            print(f"skipping {p.name}, can't read it owo")
            skipped += 1
            continue
        # imdecode on raw bytes so weird filenames can't bite us, and it also applies
        # the phone's EXIF rotation so portrait photos aren't sideways uwu
        img = cv2.imdecode(np.frombuffer(data, np.uint8), cv2.IMREAD_COLOR)
        if img is None:
            print(f"skipping {p.name}, not a readable image >_<")
            skipped += 1
            continue
        if min(img.shape[:2]) < args.window:
            print(f"skipping {p.name}, short side is under {args.window}px nya~")
            skipped += 1
            continue

        # the names are random so we name outputs by a hash of the file CONTENT ;33
        # -> no collisions between folders, same photo always gets the same name
        h = hashlib.sha1(data).hexdigest()[:10]
        # split decided by the hash too, so a photo can never hop from val to train
        # when you re-run later with more photos added (that would leak into val) uwu
        split = "val" if int(h, 16) % 1000 < args.val_frac * 1000 else "train"
        # per-photo rng seeded from the hash: reproducible, whatever order or other photos exist >_<
        rng = random.Random(f"{args.seed}-{h}")

        # val only gets plain crops, like prep_data.py does owo
        plan = [("orig", 0)] if split == "val" else [(v, r) for r in range(args.repeats) for v in VARIANTS]
        for v, r in plan:
            small = downscale(img, rng, args.min_side, args.max_side)
            window = random_window(small, rng, args.window)
            # the transforms want a segment map too, give them an all-black one and ignore it ;33
            fake_seg = np.zeros_like(window)
            win_t, seg_t = TRANSFORMS[v](window, fake_seg, rng)
            crop, _, _ = random_crop(win_t, seg_t, args.crop, rng, min_area=1)

            stem = f"neg-{h}-{v}" + (f"-{r}" if r else "")
            cv2.imwrite(str(out / "images" / split / f"{stem}.png"), crop)
            (out / "labels" / split / f"{stem}.txt").write_text("")   # empty = background nya~
            counts[split] += 1
        photos_used[split] += 1

    print(f"done! {sum(photos_used.values())} photos -> train={counts['train']} val={counts['val']} negative images uwu ;33")
    print(f"  photos in train: {photos_used['train']}, photos in val: {photos_used['val']}, skipped: {skipped}")
    if photos_used["val"] == 0:
        print("  (no photo landed in val, that's normal with few photos, the split is by hash owo)")
    print("reminder: make sure none of those photos had a milk truck in them >_<")


if __name__ == "__main__":
    main()