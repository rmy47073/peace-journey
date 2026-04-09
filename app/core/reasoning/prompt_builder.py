import json
from typing import Dict


def build_scene_prompt(scene_data: Dict) -> str:
    return json.dumps(scene_data, ensure_ascii=False, indent=2)
