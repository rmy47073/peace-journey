# 阶段 1：施工道路视觉模型训练

## 目标类别建议

- `person`
- `reflective_vest`
- `helmet`
- `mixer_truck`
- `excavator`
- `dump_truck`
- `warning_sign`

## 推荐数据准备流程

1. 收集施工道路视频，覆盖白天、夜晚、逆光、雨雾、拥堵、遮挡。
2. 使用 `train/scripts/prepare_dataset.py` 将图片和 YOLO 标签切分为 `train/val/test`。
3. 参考 `train/datasets/data.yaml.example` 生成实际的 `train/datasets/data.yaml`。
4. 使用 `train/scripts/train_detector.py` 进行微调。
5. 使用 `train/scripts/evaluate.py` 验证 mAP、Recall、Precision。
6. 使用 `train/scripts/export_onnx.py` 导出部署模型。

## 训练命令示例

```bash
python train/scripts/train_detector.py --data train/datasets/data.yaml --weights models/yolov10n.pt --epochs 100 --imgsz 960
```

## 标注建议

- 对工人额外标注 `reflective_vest`、`helmet`，为 PPE 规则提供基础。
- 对搅拌车、泥头车、挖掘机分别独立标注，便于风险分级。
- 危险区域建议额外保存为业务配置，而不是检测标签。
