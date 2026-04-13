#!/usr/bin/env python3
"""
修复文件编码问题，将 UTF-16 with BOM 转换为 UTF-8 without BOM
"""
import os

file_path = r'd:\aaaa\yolo-track-master\frontend\src\api\service.js'

# 读取文件内容（处理 UTF-16 with BOM）
with open(file_path, 'rb') as f:
    content = f.read()

# 检测并去除 BOM
if content.startswith(b'\xfe\xff'):
    text = content[2:].decode('utf-16-be')
elif content.startswith(b'\xff\xfe'):
    text = content[2:].decode('utf-16-le')
else:
    text = content.decode('utf-8')

# 保存为 UTF-8 without BOM
with open(file_path, 'w', encoding='utf-8') as f:
    f.write(text)

print(f"Successfully fixed encoding for: {file_path}")
print(f"File size: {os.path.getsize(file_path)} bytes")

# 验证结果
with open(file_path, 'rb') as f:
    new_content = f.read()
    print(f"First 10 bytes: {new_content[:10]}")
    print(f"Hex: {new_content[:10].hex()}")
