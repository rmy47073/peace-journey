import argparse
import random
import shutil
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description="Split construction-site dataset into train/val/test folders.")
    parser.add_argument("--images", required=True, help="Directory containing source images.")
    parser.add_argument("--labels", required=True, help="Directory containing YOLO label txt files.")
    parser.add_argument("--output", default="train/datasets", help="Output dataset root.")
    parser.add_argument("--train-ratio", type=float, default=0.7)
    parser.add_argument("--val-ratio", type=float, default=0.2)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    random.seed(args.seed)
    image_dir = Path(args.images)
    label_dir = Path(args.labels)
    output_dir = Path(args.output)
    image_files = [p for p in image_dir.iterdir() if p.suffix.lower() in {".jpg", ".jpeg", ".png"}]
    random.shuffle(image_files)

    train_end = int(len(image_files) * args.train_ratio)
    val_end = train_end + int(len(image_files) * args.val_ratio)
    splits = {
        "train": image_files[:train_end],
        "val": image_files[train_end:val_end],
        "test": image_files[val_end:],
    }

    for split, files in splits.items():
        images_out = output_dir / "images" / split
        labels_out = output_dir / "labels" / split
        images_out.mkdir(parents=True, exist_ok=True)
        labels_out.mkdir(parents=True, exist_ok=True)
        for image_path in files:
            label_path = label_dir / f"{image_path.stem}.txt"
            shutil.copy2(image_path, images_out / image_path.name)
            if label_path.exists():
                shutil.copy2(label_path, labels_out / label_path.name)

    print(f"Prepared dataset at {output_dir}")


if __name__ == "__main__":
    main()
