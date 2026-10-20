#!/usr/bin/env python3
"""
draw_boxes.py -- sanity checker for prep_data.py output uwu ;33

reads images/<split>/*.png + labels/<split>/*.txt (yolo format), draws the
boxes on a COPY of each image and saves them into a separate folder, so the
originals stay untouched >_< nya~

usage:
    python draw_boxes.py                       # train split, root ., out debug_boxes/
    python draw_boxes.py --split all           # train + val
    python draw_boxes.py --root milk_data --out check --limit 50
"""
import argparse
from pathlib import Path

import cv2

# colors are BGR because opencv is like that owo
COLORS = {0: (0, 255, 0), 1: (0, 128, 255)}   # class 0 green, class 1 orange uwu
NAMES = {0: "milk_truck", 1: "not_milk_truck"}  # matches milk.yaml ;33


def read_labels(path):
    """returns list of (cls, cx, cy, w, h), all normalized nya~"""
    boxes = []
    for ln, line in enumerate(path.read_text().splitlines(), 1):
        parts = line.split()
        if not parts:
            continue
        if len(parts) != 5:
            print(f"  weird line {ln} in {path.name}: '{line}' >_<")
            continue
        boxes.append((int(parts[0]), *map(float, parts[1:])))
    return boxes


def draw(img, boxes):
    H, W = img.shape[:2]
    bad = 0
    for cls, cx, cy, w, h in boxes:
        # yolo center/size -> pixel corners owo
        x1, y1 = round((cx - w / 2) * W), round((cy - h / 2) * H)
        x2, y2 = round((cx + w / 2) * W), round((cy + h / 2) * H)
        # anything poking outside the image means the label math is off ;33
        if x1 < 0 or y1 < 0 or x2 > W or y2 > H:
            bad += 1
        color = COLORS.get(cls, (255, 255, 0))
        cv2.rectangle(img, (x1, y1), (x2 - 1, y2 - 1), color, 1)
        label = NAMES.get(cls, str(cls))
        # little label just above the box, or inside if we're at the top edge uwu
        ty = y1 - 4 if y1 > 12 else y1 + 12
        cv2.putText(img, label, (max(x1, 0), ty), cv2.FONT_HERSHEY_SIMPLEX,
                    0.4, color, 1, cv2.LINE_AA)
    return bad


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=".", help="folder containing images/ and labels/ uwu")
    ap.add_argument("--out", default="debug_boxes", help="where the drawn copies go >_<")
    ap.add_argument("--split", default="train", choices=["train", "val", "all"])
    ap.add_argument("--limit", type=int, default=0, help="only do the first N images per split (0 = all) nya~")
    args = ap.parse_args()

    root, out = Path(args.root), Path(args.out)
    splits = ["train", "val"] if args.split == "all" else [args.split]

    total = boxes_total = empties = missing = out_of_bounds = 0
    for split in splits:
        img_dir, lbl_dir = root / "images" / split, root / "labels" / split
        if not img_dir.is_dir():
            print(f"no folder {img_dir}, skipping owo")
            continue
        (out / split).mkdir(parents=True, exist_ok=True)

        paths = sorted(img_dir.glob("*.png"))
        if args.limit:
            paths = paths[:args.limit]

        for p in paths:
            img = cv2.imread(str(p), cv2.IMREAD_COLOR)
            lbl = lbl_dir / f"{p.stem}.txt"
            if img is None:
                print(f"couldn't read {p.name} >_<")
                continue
            if not lbl.exists():
                # yolo treats this as background, but prep_data always writes a txt so it's suspicious ;33
                missing += 1
                boxes = []
                cv2.putText(img, "NO LABEL FILE", (4, 14), cv2.FONT_HERSHEY_SIMPLEX,
                            0.45, (0, 0, 255), 1, cv2.LINE_AA)
            else:
                boxes = read_labels(lbl)
                if not boxes:
                    empties += 1
                    cv2.putText(img, "no truck", (4, 14), cv2.FONT_HERSHEY_SIMPLEX,
                                0.45, (200, 200, 200), 1, cv2.LINE_AA)
            out_of_bounds += draw(img, boxes)
            boxes_total += len(boxes)
            total += 1
            cv2.imwrite(str(out / split / p.name), img)

    print(f"drew {boxes_total} boxes on {total} images uwu ;33")
    print(f"  empty labels (negatives): {empties}")
    print(f"  missing label files:      {missing}")
    print(f"  boxes poking outside img: {out_of_bounds}")
    print(f"look at them in: {out.resolve()} nya~")


if __name__ == "__main__":
    main()