import argparse
from ultralytics import YOLO


def main():
    parser = argparse.ArgumentParser(description="Fine-tune YOLO on construction-road dataset.")
    parser.add_argument("--data", default="train/datasets/data.yaml", help="Path to dataset yaml.")
    parser.add_argument("--weights", default="models/yolov10n.pt", help="Pretrained weights.")
    parser.add_argument("--epochs", type=int, default=100)
    parser.add_argument("--imgsz", type=int, default=960)
    parser.add_argument("--batch", type=int, default=8)
    parser.add_argument("--device", default="0")
    parser.add_argument("--project", default="train/experiments/detector")
    parser.add_argument("--name", default="construction_ft")
    args = parser.parse_args()

    model = YOLO(args.weights)
    model.train(
        data=args.data,
        epochs=args.epochs,
        imgsz=args.imgsz,
        batch=args.batch,
        device=args.device,
        project=args.project,
        name=args.name,
        pretrained=True,
    )


if __name__ == "__main__":
    main()
