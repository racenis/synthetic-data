#!/usr/bin/env python3
"""
train.py -- two stage yolo11n finetune for milk trucks, cpu only uwu ;33

stage 1: backbone frozen, only neck/head learn (fast, protects the pretrained features)
stage 2: everything unfrozen with a small learning rate (gentle polish)

usage:
    pip install ultralytics
    python train.py --epochs1 1 --skip-stage2     # tiny smoke test first, see how slow your laptop is >_<
    python train.py                               # the real thing
"""
import argparse
from pathlib import Path

from ultralytics import YOLO


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default="milk.yaml")
    ap.add_argument("--model", default="yolo11n.pt", help="gets auto-downloaded the first time owo")
    ap.add_argument("--imgsz", type=int, default=224, help="same as the crop size from prep_data.py, multiple of 32 uwu")
    ap.add_argument("--batch", type=int, default=8)
    ap.add_argument("--epochs1", type=int, default=30, help="stage 1 (frozen backbone) epochs")
    ap.add_argument("--epochs2", type=int, default=15, help="stage 2 (everything unfrozen) epochs")
    ap.add_argument("--workers", type=int, default=2, help="dataloader workers, keep low on an old laptop nya~")
    ap.add_argument("--skip-stage2", action="store_true")
    args = ap.parse_args()

    common = dict(
        data=args.data,
        imgsz=args.imgsz,
        batch=args.batch,
        device="cpu",           # no gpu here >_<
        workers=args.workers,
        cache=True,             # keep the small dataset in RAM so we don't re-decode pngs every epoch ;33
        project="runs_milk",
        exist_ok=False,         # new numbered folder each run so nothing gets overwritten uwu
    )

    # ---------- stage 1: head only ----------
    model = YOLO(args.model)
    model.train(epochs=args.epochs1, freeze=10, name="stage1", **common)  # layers 0-9 = backbone owo
    # ask the trainer where it saved things instead of guessing the path ;33
    best1 = Path(model.trainer.save_dir) / "weights" / "best.pt"
    print(f"stage 1 done, best weights: {best1} uwu")

    if args.skip_stage2:
        return

    # ---------- stage 2: unfreeze + low lr ----------
    model = YOLO(str(best1))
    # optimizer must be explicit, otherwise 'auto' silently ignores lr0 (found that out in testing >_<)
    model.train(epochs=args.epochs2, optimizer="AdamW", lr0=0.0005, warmup_epochs=0,
                name="stage2", **common)
    best2 = Path(model.trainer.save_dir) / "weights" / "best.pt"
    print(f"stage 2 done, best weights: {best2} nya~")
    print("compare the val mAP50-95 of both stages and keep whichever is better >_<")


if __name__ == "__main__":
    main()
