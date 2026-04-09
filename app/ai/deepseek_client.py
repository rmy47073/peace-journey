# -*- coding: utf-8 -*-
"""
DeepSeek大模型客户端
支持通过API调用DeepSeek进行智能推理和决策
"""
import requests
import json
from typing import Dict, List, Optional


class DeepSeekClient:
    """DeepSeek API客户端"""

    def __init__(self, api_key: str, base_url: str = "https://api.deepseek.com/v1"):
        """
        初始化DeepSeek客户端

        Args:
            api_key: DeepSeek API密钥
            base_url: API基础URL
        """
        self.api_key = api_key
        self.base_url = base_url
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

    def chat_completion(self,
                       messages: List[Dict[str, str]],
                       model: str = "deepseek-chat",
                       temperature: float = 0.7,
                       max_tokens: int = 2000) -> Optional[str]:
        """
        调用DeepSeek聊天完成API

        Args:
            messages: 消息列表 [{"role": "user", "content": "..."}]
            model: 模型名称
            temperature: 温度参数
            max_tokens: 最大token数

        Returns:
            模型响应文本
        """
        try:
            payload = {
                "model": model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens
            }

            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=self.headers,
                json=payload,
                timeout=30
            )

            if response.status_code == 200:
                result = response.json()
                return result["choices"][0]["message"]["content"]
            else:
                print(f"[DeepSeek] API错误: {response.status_code} - {response.text}")
                return None

        except Exception as e:
            print(f"[DeepSeek] 调用异常: {str(e)}")
            return None

    def analyze_scene(self, scene_data: Dict) -> Optional[Dict]:
        """
        分析施工场景并给出决策建议

        Args:
            scene_data: 场景数据字典，包含检测到的对象、位置等信息

        Returns:
            分析结果和建议
        """
        prompt = self._build_scene_analysis_prompt(scene_data)

        messages = [
            {"role": "system", "content": "你是一个施工安全监控专家，负责分析施工现场的安全状况并提供预警建议。"},
            {"role": "user", "content": prompt}
        ]

        response = self.chat_completion(messages, temperature=0.3)

        if response:
            try:
                # 尝试解析JSON响应
                return json.loads(response)
            except json.JSONDecodeError:
                return {"analysis": response, "risk_level": "unknown"}
        return None

    def _build_scene_analysis_prompt(self, scene_data: Dict) -> str:
        """构建场景分析提示词"""
        prompt = f"""
请分析以下施工现场监控数据，评估安全风险并给出建议：

检测对象：
- 车辆数量: {scene_data.get('vehicle_count', 0)}
- 工人数量: {scene_data.get('worker_count', 0)}
- 施工设备: {scene_data.get('equipment', [])}

区域信息：
- 危险区域内对象: {scene_data.get('danger_zone_objects', [])}
- 安全区域违规: {scene_data.get('safety_violations', [])}

运动状态：
- 快速移动车辆: {scene_data.get('fast_vehicles', [])}
- 异常停留: {scene_data.get('abnormal_stays', [])}

请以JSON格式返回分析结果：
{{
    "risk_level": "low/medium/high/critical",
    "risks": ["风险1", "风险2"],
    "suggestions": ["建议1", "建议2"],
    "immediate_actions": ["立即行动1"],
    "reasoning": "分析推理过程"
}}
"""
        return prompt
