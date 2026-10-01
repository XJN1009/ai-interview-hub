"""AI 服务配置的读写与缓存。

优先级：数据库 system_settings > .env/默认值（settings）。
自部署场景下，用户可在登录前通过配置向导填写自己的 API-KEY 与 Base URL，
保存后立即生效，无需修改 .env 或重启服务。
"""
import json
import logging
from typing import Optional

import httpx
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.system import SystemSetting

logger = logging.getLogger("ai_settings")

# 数据库中的配置键
KEY_MODE = "ai_mode"
KEY_BASE_URL = "llm_base_url"
KEY_API_KEY = "llm_api_key"
KEY_MODEL = "llm_model"

# 进程内缓存：配置读取远多于写入，保存时主动失效
_cache: Optional[dict] = None


def mask_key(api_key: str) -> str:
    """脱敏展示 API Key，仅保留头尾少量字符。"""
    if not api_key:
        return ""
    if len(api_key) <= 8:
        return "•" * len(api_key)
    return api_key[:3] + "•" * 8 + api_key[-4:]


def get_effective_config(db: Optional[Session] = None) -> dict:
    """返回当前生效的 AI 配置（DB 覆盖 .env 默认值），带进程内缓存。"""
    global _cache
    if _cache is not None:
        return dict(_cache)

    overrides = {}
    if db is not None:
        rows = db.query(SystemSetting).filter(
            SystemSetting.key.in_([KEY_MODE, KEY_BASE_URL, KEY_API_KEY, KEY_MODEL])
        ).all()
        overrides = {r.key: (r.value or "") for r in rows}

    config = {
        "mode": (overrides.get(KEY_MODE) or settings.AI_MODE or "real").strip().lower(),
        "base_url": overrides.get(KEY_BASE_URL) or settings.LLM_BASE_URL,
        "api_key": overrides.get(KEY_API_KEY) or settings.LLM_API_KEY,
        "model": overrides.get(KEY_MODEL) or settings.LLM_MODEL,
        "configured": bool(overrides.get(KEY_API_KEY) or settings.LLM_API_KEY),
    }
    _cache = dict(config)
    return config


def invalidate_cache() -> None:
    global _cache
    _cache = None


def save_config(db: Session, data: dict) -> dict:
    """保存配置（仅更新提交的字段；api_key 传空字符串表示保持不变）。"""
    mapping = {
        "mode": (KEY_MODE, lambda v: str(v).strip().lower()),
        "base_url": (KEY_BASE_URL, lambda v: str(v).strip().rstrip("/")),
        "api_key": (KEY_API_KEY, lambda v: str(v).strip()),
        "model": (KEY_MODEL, lambda v: str(v).strip()),
    }
    for field, (key, normalizer) in mapping.items():
        if field not in data or data[field] is None:
            continue
        value = normalizer(data[field])
        if field == "api_key" and value == "":
            continue  # 空 Key 视为"不修改"
        row = db.query(SystemSetting).filter(SystemSetting.key == key).first()
        if row:
            row.value = value
        else:
            db.add(SystemSetting(key=key, value=value))
    db.commit()
    invalidate_cache()
    return get_effective_config(db)


def validate_base_url(base_url: str) -> Optional[str]:
    """校验 Base URL 仅允许 http/https 协议，返回错误信息或 None。"""
    if not base_url:
        return "Base URL 不能为空"
    if not base_url.startswith(("http://", "https://")):
        return "Base URL 必须以 http:// 或 https:// 开头"
    return None


async def test_connection(base_url: str, api_key: str, model: str) -> dict:
    """向目标端点发送一条最小 chat 请求验证配置有效性。"""
    err = validate_base_url(base_url)
    if err:
        return {"success": False, "message": err}
    if not api_key:
        return {"success": False, "message": "API Key 不能为空"}

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": model or "gpt-4o-mini",
        "messages": [{"role": "user", "content": "ping"}],
        "max_tokens": 1,
    }
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            res = await client.post(f"{base_url}/chat/completions", headers=headers, json=payload)
            if res.status_code == 200:
                return {"success": True, "message": "连接成功，API Key 与模型可用"}
            body = res.text[:300]
            return {"success": False, "message": f"服务返回 {res.status_code}: {body}"}
    except httpx.TimeoutException:
        return {"success": False, "message": "连接超时（15 秒），请检查 Base URL 与网络"}
    except Exception as e:
        return {"success": False, "message": f"连接失败: {e}"}
