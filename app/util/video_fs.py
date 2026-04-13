# -*- coding: utf-8 -*-
"""videos 目录下列表与安全路径校验"""
import os

import cv2

VIDEO_EXTENSIONS = frozenset({".mp4", ".avi", ".mov", ".mkv", ".webm", ".m4v", ".wmv"})


def list_video_files(folder_path: str = "./videos"):
    if not os.path.isdir(folder_path):
        return []
    names = []
    for f in os.listdir(folder_path):
        p = os.path.join(folder_path, f)
        if os.path.isfile(p) and os.path.splitext(f)[1].lower() in VIDEO_EXTENSIONS:
            names.append(f)
    return sorted(names, key=str.lower)


def resolve_safe_video_file(cap_path: str):
    """
    校验 cap_path 必须位于项目 videos/ 目录下的真实文件。
    返回规范化的 posix 风格相对路径（如 videos/a.mp4），非法则返回 None。
    """
    if not cap_path or not isinstance(cap_path, str):
        return None
    raw = cap_path.strip().replace("\\", "/")
    if ".." in raw or raw.startswith("/"):
        return None
    if not raw.startswith("videos/"):
        return None
    full = os.path.normpath(os.path.join(os.getcwd(), raw))
    root = os.path.normpath(os.path.join(os.getcwd(), "videos"))
    try:
        if os.path.commonpath([full, root]) != root:
            return None
    except ValueError:
        return None
    if not os.path.isfile(full):
        return None
    return raw


def file_frame_period_seconds(cap) -> float:
    """
    本地视频按真实时间播放时每帧周期（秒）。0 表示不节流。
    需在 app.config 已加载后调用（读取 SYNC_VIDEO_FILE_TO_REALTIME 等）。
    """
    from app.config.config import Config

    if not getattr(Config, "SYNC_VIDEO_FILE_TO_REALTIME", True):
        return 0.0
    fps = cap.get(cv2.CAP_PROP_FPS)
    try:
        fps = float(fps)
    except (TypeError, ValueError):
        fps = 0.0
    if fps <= 1.0 or fps > 120.0:
        fps = float(getattr(Config, "VIDEO_FILE_FALLBACK_FPS", 25.0))
    return 1.0 / fps
