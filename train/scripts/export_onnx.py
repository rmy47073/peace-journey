import argparse
from ultralytics import YOLO


def main():
    parser = argparse.ArgumentParser(description="Export YOLO weights to ONNX for deployment.")
    parser.add_argument("--weights", required=True, help="Path to trained weights.")
    parser.add_argument("--imgsz", type=int, default=960)
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--half", action="store_true")
    args = parser.parse_args()

    model = YOLO(args.weights)
    model.export(format="onnx", imgsz=args.imgsz, device=args.device, half=args.half)


if __name__ == "__main__":
    main()
