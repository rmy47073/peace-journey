import argparse
from ultralytics import YOLO


def main():
    parser = argparse.ArgumentParser(description="Evaluate a trained YOLO model.")
    parser.add_argument("--weights", required=True, help="Path to trained model weights.")
    parser.add_argument("--data", default="train/datasets/data.yaml", help="Dataset yaml.")
    parser.add_argument("--imgsz", type=int, default=960)
    parser.add_argument("--device", default="0")
    args = parser.parse_args()

    model = YOLO(args.weights)
    metrics = model.val(data=args.data, imgsz=args.imgsz, device=args.device)
    print(metrics)


if __name__ == "__main__":
    main()
