#!/usr/bin/env python3
"""
prep_data.py -- turns N-image.png / N-segment.png pairs into a YOLO dataset uwu ;33

for every source pair we make 5 variants (orig, flip, hsv, warp, skew),
random crop each one, pull bounding boxes out of the magenta pixels in the
segment map, and write images + yolo txt labels >_< nya~

output layout (default is the working dir, so you get ./images/ like you wanted):
    images/train/*.png   labels/train/*.txt
    images/val/*.png     labels/val/*.txt

usage:
    python prep_data.py                      # sources in ., output in .
    python prep_data.py --src gen --out milk_data --seed 123
"""
import argparse
import random
import re
from pathlib import Path

import cv2
import numpy as np

# magenta in BGR is still (255, 0, 255) because B and R are both 255 owo
# (cv2 loads as BGR, lucky that the color is symmetric >_<)
MILK_BGR = (255, 0, 255)

VARIANTS = ["orig", "flip", "hsv", "warp", "skew"]


# ---------- transformations (all take + return (img, seg)) ----------

def t_orig(img, seg, rng):
    return img, seg  # nothing to do, just vibes uwu


def t_flip(img, seg, rng):
    # same flip for both so the mask stays glued to the truck ;33
    return cv2.flip(img, 1), cv2.flip(seg, 1)


def t_hsv(img, seg, rng):
    # color-only change, segment must NOT be touched or the magenta breaks >_<
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV).astype(np.int16)
    hsv[..., 0] = (hsv[..., 0] + rng.randint(-25, 25)) % 180      # hue wraps at 180 in cv2 nya~
    hsv[..., 1] = hsv[..., 1] * rng.uniform(0.6, 1.4)             # saturation owo
    hsv[..., 2] = hsv[..., 2] * rng.uniform(0.7, 1.3)             # brightness uwu
    hsv = np.clip(hsv, 0, 255).astype(np.uint8)
    return cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR), seg


def _remap_pair(img, seg, map_x, map_y):
    # image gets smooth interpolation, segment gets NEAREST so magenta stays
    # exactly (255, 0, 255) and doesn't blend into weird colors >_< ;33
    # border is constant black, NOT reflect, otherwise trucks would get cloned uwu
    img_w = cv2.remap(img, map_x, map_y, cv2.INTER_LINEAR,
                      borderMode=cv2.BORDER_CONSTANT, borderValue=0)
    seg_w = cv2.remap(seg, map_x, map_y, cv2.INTER_NEAREST,
                      borderMode=cv2.BORDER_CONSTANT, borderValue=0)
    return img_w, seg_w


def t_warp(img, seg, rng):
    # wobbly sine-wave warp, like looking through wavy glass owo
    h, w = img.shape[:2]
    ys, xs = np.mgrid[0:h, 0:w].astype(np.float32)
    amp_x, amp_y = rng.uniform(3, 9), rng.uniform(3, 9)
    wl_x, wl_y = rng.uniform(70, 160), rng.uniform(70, 160)
    ph_x, ph_y = rng.uniform(0, 6.28), rng.uniform(0, 6.28)
    map_x = xs + amp_x * np.sin(2 * np.pi * ys / wl_x + ph_x)
    map_y = ys + amp_y * np.sin(2 * np.pi * xs / wl_y + ph_y)
    return _remap_pair(img, seg, map_x.astype(np.float32), map_y.astype(np.float32))


def t_skew(img, seg, rng):
    # shear along a random axis, shear center is the image center nya~
    h, w = img.shape[:2]
    s = rng.uniform(0.12, 0.3) * rng.choice([-1, 1])
    if rng.random() < 0.5:   # horizontal shear uwu
        M = np.float32([[1, s, -s * h / 2], [0, 1, 0]])
    else:                    # vertical shear >_<
        M = np.float32([[1, 0, 0], [s, 1, -s * w / 2]])
    img_w = cv2.warpAffine(img, M, (w, h), flags=cv2.INTER_LINEAR,
                           borderMode=cv2.BORDER_CONSTANT, borderValue=0)
    seg_w = cv2.warpAffine(seg, M, (w, h), flags=cv2.INTER_NEAREST,
                           borderMode=cv2.BORDER_CONSTANT, borderValue=0)
    return img_w, seg_w


TRANSFORMS = {"orig": t_orig, "flip": t_flip, "hsv": t_hsv, "warp": t_warp, "skew": t_skew}


# ---------- cropping + boxes ----------

def get_boxes(seg, min_area):
    """returns (boxes, has_sliver). boxes are (x, y, w, h) in pixels uwu"""
    mask = np.all(seg == MILK_BGR, axis=-1).astype(np.uint8)
    n, _, stats, _ = cv2.connectedComponentsWithStats(mask, connectivity=8)
    boxes, has_sliver = [], False
    for i in range(1, n):  # 0 is background owo
        x, y, w, h, area = stats[i]
        if area < min_area:
            has_sliver = True   # tiny leftover bit of truck, probably cut by the crop ;33
        else:
            boxes.append((int(x), int(y), int(w), int(h)))
    return boxes, has_sliver


def random_crop(img, seg, size, rng, min_area, tries=10):
    h, w = img.shape[:2]
    for _ in range(tries):
        x0 = rng.randint(0, w - size)
        y0 = rng.randint(0, h - size)
        seg_c = seg[y0:y0 + size, x0:x0 + size]
        boxes, sliver = get_boxes(seg_c, min_area)
        if not sliver:   # crop didn't leave any weird half-truck crumbs nya~
            break
    # if every try had slivers we just keep the last one, slivers get dropped from labels >_<
    return img[y0:y0 + size, x0:x0 + size], seg_c, boxes


def to_yolo_line(box, size):
    x, y, w, h = box
    cx, cy = (x + w / 2) / size, (y + h / 2) / size
    return f"0 {cx:.6f} {cy:.6f} {w / size:.6f} {h / size:.6f}"  # class 0 = milk_truck uwu


# ---------- main ----------

def find_pairs(src):
    pairs = []
    for p in src.iterdir():
        m = re.fullmatch(r"(\d+)-image\.png", p.name)
        if m and (src / f"{m.group(1)}-segment.png").exists():
            pairs.append(int(m.group(1)))
    return sorted(pairs)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", default=".", help="where the N-image.png files live uwu")
    ap.add_argument("--out", default=".", help="output root, gets images/ and labels/ >_<")
    ap.add_argument("--crop", type=int, default=224)
    ap.add_argument("--val-frac", type=float, default=0.1, help="fraction of SOURCE ids for val")
    ap.add_argument("--min-area", type=int, default=64, help="components smaller than this (px) are slivers")
    ap.add_argument("--seed", type=int, default=0)
    args = ap.parse_args()

    rng = random.Random(args.seed)
    src, out = Path(args.src), Path(args.out)

    ids = find_pairs(src)
    if not ids:
        raise SystemExit("no N-image.png / N-segment.png pairs found, nyo~ >_<")

    # split by SOURCE id, so a flipped copy of a train image can never sneak into val ;33
    shuffled = ids[:]
    rng.shuffle(shuffled)
    n_val = max(1, int(len(ids) * args.val_frac)) if len(ids) > 1 else 0
    val_ids = set(shuffled[:n_val])

    for split in ("train", "val"):
        (out / "images" / split).mkdir(parents=True, exist_ok=True)
        (out / "labels" / split).mkdir(parents=True, exist_ok=True)

    counts = {"train": 0, "val": 0}
    empties = 0
    for i in ids:
        img = cv2.imread(str(src / f"{i}-image.png"), cv2.IMREAD_COLOR)
        seg = cv2.imread(str(src / f"{i}-segment.png"), cv2.IMREAD_COLOR)
        if img is None or seg is None or img.shape != seg.shape:
            print(f"skipping {i}, couldn't read it or sizes don't match owo")
            continue
        if min(img.shape[:2]) < args.crop:
            print(f"skipping {i}, smaller than the crop size >_<")
            continue

        split = "val" if i in val_ids else "train"
        # val only gets the plain variant so it looks like 'real' data uwu
        variants = ["orig"] if split == "val" else VARIANTS

        for v in variants:
            img_t, seg_t = TRANSFORMS[v](img, seg, rng)
            img_c, seg_c, boxes = random_crop(img_t, seg_t, args.crop, rng, args.min_area)

            stem = f"{i}-{v}"
            cv2.imwrite(str(out / "images" / split / f"{stem}.png"), img_c)
            lines = [to_yolo_line(b, args.crop) for b in boxes]
            # no trucks -> empty txt file, which yolo reads as a negative sample nya~
            (out / "labels" / split / f"{stem}.txt").write_text("\n".join(lines) + ("\n" if lines else ""))
            counts[split] += 1
            empties += not boxes

    print(f"done! train={counts['train']} val={counts['val']} images, "
          f"{empties} with no truck (negatives) uwu ;33")
    print(f"dataset root for milk.yaml: {out.resolve()}")


if __name__ == "__main__":
    main()