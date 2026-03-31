import argparse
import os
from typing import Tuple

from PIL import Image


def _list_images(d: str):
    return sorted([f for f in os.listdir(d) if f.lower().endswith((".png", ".jpg", ".jpeg"))])


def _image_size(p: str) -> Tuple[int, int]:
    im = Image.open(p)
    return im.size


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--src-dir", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--scale", type=int, default=2)
    args = ap.parse_args()

    src_dir = os.path.abspath(args.src_dir)
    out_dir = os.path.abspath(args.out_dir)
    os.makedirs(out_dir, exist_ok=True)

    files = _list_images(src_dir)
    total = len(files)
    done = 0
    skipped = 0

    for i, f in enumerate(files):
        src_p = os.path.join(src_dir, f)
        out_p = os.path.join(out_dir, f)

        if os.path.exists(out_p):
            skipped += 1
            continue

        im = Image.open(src_p).convert("RGB")
        w, h = im.size
        im2 = im.resize((w * args.scale, h * args.scale), resample=Image.NEAREST)
        im2.save(out_p)
        done += 1

        if (i + 1) % 200 == 0:
            print(f"[{i+1}/{total}] done={done} skipped={skipped}")

    if files:
        src0 = os.path.join(src_dir, files[0])
        out0 = os.path.join(out_dir, files[0])
        print("src_sample", src0, "size", _image_size(src0))
        print("out_sample", out0, "size", _image_size(out0))

    print(f"total={total} done={done} skipped={skipped} out_dir={out_dir}")


if __name__ == "__main__":
    main()
