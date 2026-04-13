# -*- coding: utf-8 -*-
"""
DeepSeek大模型客户端
支持通过API调用DeepSeek进行智能推理和决策
"""
import re
import requests
import json
from typing import Dict, List, Optional


def _parse_model_json_response(text: str) -> Optional[Dict]:
    """解析模型输出：纯 JSON 或 ```json ... ``` 包裹。"""
    if not text or not str(text).strip():
        return None
    s = str(text).strip()
    m = re.search(r"```(?:json)?\s*([\s\S]*?)```", s, re.IGNORECASE)
    if m:
        s = m.group(1).strip()
    try:
        obj = json.loads(s)
        return obj if isinstance(obj, dict) else None
    except json.JSONDecodeError:
        pass
    try:
        start = s.find("{")
        end = s.rfind("}")
        if start >= 0 and end > start:
            return json.loads(s[start : end + 1])
    except json.JSONDecodeError:
        pass
    return None


class DeepSeekClient:
    """DeepSeek / OpenAI兼容API客户端"""

    def __init__(self, api_key: str, base_url: str = "https://api.deepseek.com/v1", provider: str = "deepseek_api"):
        """
        初始化DeepSeek客户端

        Args:
            api_key: DeepSeek API密钥
            base_url: API基础URL
        """
        self.api_key = api_key
        self.base_url = base_url
        self.provider = provider
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        self.last_error: Optional[str] = None

    def chat_completion(self,
                       messages: List[Dict[str, str]],
                       model: str = "deepseek-chat",
                       temperature: float = 0.7,
                       max_tokens: int = 2000,
                       timeout: int = 30) -> Optional[str]:
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
        self.last_error = None
        url = f"{self.base_url.rstrip('/')}/chat/completions"
        try:
            payload = {
                "model": model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens
            }

            response = requests.post(
                url,
                headers=self.headers,
                json=payload,
                timeout=timeout,
            )

            if response.status_code == 200:
                try:
                    result = response.json()
                except json.JSONDecodeError as e:
                    self.last_error = f"响应非 JSON: {e}"
                    print(f"[DeepSeek] {self.last_error}")
                    return None
                choices = result.get("choices")
                if not choices:
                    self.last_error = f"响应无 choices 字段: {str(result)[:400]}"
                    print(f"[DeepSeek] {self.last_error}")
                    return None
                msg = choices[0].get("message") or {}
                content = msg.get("content")
                if content is None or (isinstance(content, str) and not content.strip()):
                    self.last_error = "响应 content 为空"
                    print(f"[DeepSeek] {self.last_error}")
                    return None
                return content
            err_body = (response.text or "")[:800]
            if response.status_code == 402:
                hint = "（账户余额不足，请到 https://platform.deepseek.com 充值或更换有余额的 API Key）"
                self.last_error = f"HTTP 402 Insufficient Balance{hint} 原始响应: {err_body}"
            elif response.status_code == 401:
                self.last_error = f"HTTP 401 密钥无效或已过期，请检查 DEEPSEEK_API_KEY。响应: {err_body}"
            else:
                self.last_error = f"HTTP {response.status_code}: {err_body}"
            print(f"[DeepSeek] API错误: {self.last_error}")

        except requests.exceptions.Timeout:
            self.last_error = f"请求超时（>{timeout}s），请检查网络或增大 LLM_TIMEOUT"
            print(f"[DeepSeek] {self.last_error}")
        except requests.exceptions.ConnectionError as e:
            self.last_error = f"无法连接 {url}：{e}"
            print(f"[DeepSeek] {self.last_error}")
        except Exception as e:
            self.last_error = f"{type(e).__name__}: {e}"
            print(f"[DeepSeek] 调用异常: {self.last_error}")
        return None

    def analyze_scene(self, scene_data: Dict, rules_result: Optional[Dict] = None, system_prompt: Optional[str] = None,
                      model: str = "deepseek-chat", temperature: float = 0.3,
                      max_tokens: int = 1200, timeout: int = 30) -> Optional[Dict]:
        """
        分析施工场景并给出决策建议

        Args:
            scene_data: 场景数据字典，包含检测到的对象、位置等信息

        Returns:
            分析结果和建议
        """
        prompt = self._build_scene_analysis_prompt(scene_data, rules_result)

        messages = [
            {
                "role": "system",
                "content": system_prompt or "你是一个施工安全监控专家，负责分析施工现场的安全状况并提供预警建议。"
            },
            {"role": "user", "content": prompt}
        ]

        response = self.chat_completion(
            messages,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            timeout=timeout,
        )

        if not response:
            return None

        parsed = _parse_model_json_response(response)
        if parsed:
            return parsed

        return {
            "analysis": response,
            "risk_level": "medium",
            "risks": ["模型返回了非 JSON 格式，以下为原文摘要，请人工查看"],
            "suggestions": ["请在后端日志中查看完整模型输出，或调整提示词要求仅输出 JSON"],
            "reasoning": response[:1200] if len(response) > 1200 else response,
        }

    def _build_scene_analysis_prompt(self, scene_data: Dict, rules_result: Optional[Dict] = None) -> str:
        """构建场景分析提示词"""
        rules_result = rules_result or {}
        prompt = f"""
请分析以下施工现场监控数据，评估安全风险并给出建议。
请重点关注车辆超速、人员闯入危险区域、人车距离过近、违规停留与未佩戴安全装备等风险。

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
- 规则引擎结果: {rules_result}

请以JSON格式返回分析结果（不要省略 risks，至少填写 1 条具体风险描述）：
{{
    "risk_level": "low/medium/high/critical",
    "risks": ["风险1", "风险2"],
    "suggestions": ["建议1", "建议2"],
    "immediate_actions": ["立即行动1"],
    "reasoning": "分析推理过程"
}}
即使当前画面看似正常，也请从施工道路安全角度给出至少一条「需注意」的 risks 条目。
"""
        return prompt
