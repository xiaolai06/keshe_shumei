"""
智居物语 — 全局配置
支持从 data/config.json 持久化 LLM 配置
"""
import json
import os
from pathlib import Path

# ══════════════════════════════════════════════
# 路径
# ══════════════════════════════════════════════
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
FACES_DIR = DATA_DIR / "faces"
SNAPSHOTS_DIR = DATA_DIR / "snapshots"
LOGS_DIR = DATA_DIR / "logs"
MODELS_DIR = BASE_DIR / "models"
FONT_PATH = BASE_DIR / "fonts" / "simhei.ttf"

# ══════════════════════════════════════════════
# STT 语音识别（云端 API）
# ══════════════════════════════════════════════
STT_API_KEY = ""          # 可以和 LLM 共用 key
STT_BASE_URL = "https://api.openai.com/v1"
STT_MODEL = "whisper-1"
STT_LANGUAGE = "zh"       # 识别语言

# ══════════════════════════════════════════════
# LLM
# ══════════════════════════════════════════════
LLM_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
LLM_BASE_URL = os.getenv("LLM_BASE_URL", "https://api.deepseek.com/v1")
LLM_MODEL = os.getenv("LLM_MODEL", "deepseek-chat")
LLM_TEMPERATURE = 0.7
LLM_MAX_TOKENS = 512

# ══════════════════════════════════════════════
# 硬件引脚 (BCM 编号)
# ══════════════════════════════════════════════

# ── 传感器（输入） ──
PIN_DS18B20 = 4          # DS18B20 温度传感器 (1-Wire, GPIO 4, 物理7)
PIN_DHT22 = 17           # DHT22 温湿度传感器 (单总线, GPIO 17, 物理11)
PIN_LIGHT = 27           # 光照传感器数字输出 (GPIO 27, 物理13)

# ── 输出设备 ──
PIN_BUZZER = 12          # 有源蜂鸣器模块 (GPIO 12, 物理32)

# ── SPI (OLED 独占 SPI0 总线) ──
OLED_SPI_CS = 8          # SSD1351 OLED 片选 CE0 (GPIO 8, 物理24)
OLED_SPI_DC = 13         # SSD1351 OLED 数据/命令 (GPIO 13, 物理33)
OLED_SPI_RST = 24        # SSD1351 OLED 复位 (GPIO 24, 物理18)

# ── I2S (INMP441 麦克风) ──
I2S_BCLK = 18            # I2S 位时钟 (GPIO 18, 物理12)
I2S_LRCK = 19            # I2S 字选择 (GPIO 19, 物理35)
I2S_DIN = 20             # I2S 数据输入 (GPIO 20, 物理38)

# ══════════════════════════════════════════════
# 情绪系统
# ══════════════════════════════════════════════
MOOD_EMA_ALPHA = 0.3          # EMA 平滑系数
MOOD_SWITCH_MIN_COUNT = 3     # 连续 N 次一致才切换
MOOD_SWITCH_MIN_DURATION = 30 # 最短持续秒数
MOOD_IDLE_THRESHOLD = 4 * 3600  # 无互动阈值（秒）

# ══════════════════════════════════════════════
# 记忆系统
# ══════════════════════════════════════════════
WORKING_MEMORY_SIZE = 10      # 工作记忆轮数
SHORT_TERM_RETAIN_DAYS = 7    # 短期记忆保留天数
LONG_TERM_TOP_K = 5           # 语义检索返回数
REFLECT_THRESHOLD = 20        # 积累 N 条后触发反思

# ══════════════════════════════════════════════
# 人脸识别
# ══════════════════════════════════════════════
FACE_MATCH_THRESHOLD = 0.6

# ══════════════════════════════════════════════
# 传感器轮询
# ══════════════════════════════════════════════
SENSOR_POLL_INTERVAL = 10  # 秒

# ══════════════════════════════════════════════
# 语音监听 (VAD) 参数
# ══════════════════════════════════════════════
VOICE_ENERGY_THRESHOLD = 500       # 能量阈值（低于此值算静音，需根据环境调整）
VOICE_SILENCE_MS = 1500            # 连续静音多少毫秒算说完一句话
VOICE_MIN_SPEECH_MS = 500          # 最短语音段（太短忽略，防误触发）
VOICE_MAX_SPEECH_S = 30            # 单段语音最长秒数（防无限录音）

# ══════════════════════════════════════════════
# 服务开关（默认全部关闭，需要时手动开启）
# ══════════════════════════════════════════════
SERVICE_WEB_ENABLED = False        # 是否启动 Web 服务器
SERVICE_SENSOR_ENABLED = False     # 是否启动传感器轮询
SERVICE_REMINDER_ENABLED = False   # 是否启动提醒调度器
SERVICE_VOICE_ENABLED = False      # 是否启动语音监听

# ══════════════════════════════════════════════
# Web
# ══════════════════════════════════════════════
WEB_HOST = "0.0.0.0"
WEB_PORT = 8000

# ══════════════════════════════════════════════
# LLM 配置持久化
# ══════════════════════════════════════════════
_CONFIG_FILE = DATA_DIR / "config.json"

# 预设的 API 提供商模板
LLM_PRESETS = {
    "deepseek": {
        "name": "DeepSeek",
        "base_url": "https://api.deepseek.com/v1",
        "default_model": "deepseek-chat",
    },
    "siliconflow": {
        "name": "硅基流动 (SiliconFlow)",
        "base_url": "https://api.siliconflow.cn/v1",
        "default_model": "deepseek-ai/DeepSeek-V3",
    },
    "openai": {
        "name": "OpenAI",
        "base_url": "https://api.openai.com/v1",
        "default_model": "gpt-4o-mini",
    },
    "moonshot": {
        "name": "Moonshot (Kimi)",
        "base_url": "https://api.moonshot.cn/v1",
        "default_model": "moonshot-v1-8k",
    },
    "zhipu": {
        "name": "智谱 (GLM)",
        "base_url": "https://open.bigmodel.cn/api/paas/v4",
        "default_model": "glm-4-flash",
    },
    "qwen": {
        "name": "通义千问",
        "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
        "default_model": "qwen-turbo",
    },
    "custom": {
        "name": "自定义",
        "base_url": "",
        "default_model": "",
    },
}


def load_llm_config() -> dict:
    """从 JSON 文件加载 LLM 配置，不存在则返回当前 config 值"""
    if _CONFIG_FILE.exists():
        try:
            with open(_CONFIG_FILE, encoding="utf-8") as f:
                data = json.load(f)
            if "llm" in data:
                llm = data["llm"]
                # 回写到模块级变量
                global LLM_API_KEY, LLM_BASE_URL, LLM_MODEL, LLM_TEMPERATURE, LLM_MAX_TOKENS
                LLM_API_KEY = llm.get("api_key", LLM_API_KEY)
                LLM_BASE_URL = llm.get("base_url", LLM_BASE_URL)
                LLM_MODEL = llm.get("model", LLM_MODEL)
                LLM_TEMPERATURE = llm.get("temperature", LLM_TEMPERATURE)
                LLM_MAX_TOKENS = llm.get("max_tokens", LLM_MAX_TOKENS)
                return llm
        except (json.JSONDecodeError, OSError):
            pass
    return {
        "provider": "deepseek",
        "api_key": LLM_API_KEY,
        "base_url": LLM_BASE_URL,
        "model": LLM_MODEL,
        "temperature": LLM_TEMPERATURE,
        "max_tokens": LLM_MAX_TOKENS,
    }


def save_llm_config(llm_cfg: dict) -> None:
    """保存 LLM 配置到 JSON 文件"""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    existing = {}
    if _CONFIG_FILE.exists():
        try:
            with open(_CONFIG_FILE, encoding="utf-8") as f:
                existing = json.load(f)
        except (json.JSONDecodeError, OSError):
            pass
    old_key = existing.get("llm", {}).get("api_key", LLM_API_KEY)
    # 如果前端传来的 key 是空的或脱敏的，保留原来的
    new_key = llm_cfg.get("api_key", "")
    if not new_key or "****" in new_key:
        llm_cfg["api_key"] = old_key
    existing["llm"] = llm_cfg
    with open(_CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(existing, f, ensure_ascii=False, indent=2)
    global LLM_API_KEY, LLM_BASE_URL, LLM_MODEL, LLM_TEMPERATURE, LLM_MAX_TOKENS
    LLM_API_KEY = llm_cfg.get("api_key", LLM_API_KEY)
    LLM_BASE_URL = llm_cfg.get("base_url", LLM_BASE_URL)
    LLM_MODEL = llm_cfg.get("model", LLM_MODEL)
    LLM_TEMPERATURE = llm_cfg.get("temperature", LLM_TEMPERATURE)
    LLM_MAX_TOKENS = llm_cfg.get("max_tokens", LLM_MAX_TOKENS)


def get_llm_config_safe() -> dict:
    """获取 LLM 配置，API Key 脱敏"""
    cfg = load_llm_config()
    key = cfg.get("api_key", "")
    masked = key[:8] + "****" + key[-4:] if len(key) > 12 else ("****" if key else "")
    return {**cfg, "api_key": masked}


# ══════════════════════════════════════════════
# STT 配置持久化
# ══════════════════════════════════════════════
STT_PRESETS = {
    "siliconflow": {
        "name": "硅基流动 (SiliconFlow)",
        "base_url": "https://api.siliconflow.cn/v1",
        "default_model": "FunAudioLLM/SenseVoiceSmall",
    },
    "openai": {
        "name": "OpenAI Whisper",
        "base_url": "https://api.openai.com/v1",
        "default_model": "whisper-1",
    },
    "custom": {
        "name": "自定义",
        "base_url": "",
        "default_model": "",
    },
}


def load_stt_config() -> dict:
    """从 JSON 文件加载 STT 配置"""
    if _CONFIG_FILE.exists():
        try:
            with open(_CONFIG_FILE, encoding="utf-8") as f:
                data = json.load(f)
            if "stt" in data:
                stt = data["stt"]
                global STT_API_KEY, STT_BASE_URL, STT_MODEL, STT_LANGUAGE
                STT_API_KEY = stt.get("api_key", STT_API_KEY)
                STT_BASE_URL = stt.get("base_url", STT_BASE_URL)
                STT_MODEL = stt.get("model", STT_MODEL)
                STT_LANGUAGE = stt.get("language", STT_LANGUAGE)
                return stt
        except (json.JSONDecodeError, OSError):
            pass
    return {
        "provider": "openai",
        "api_key": STT_API_KEY,
        "base_url": STT_BASE_URL,
        "model": STT_MODEL,
        "language": STT_LANGUAGE,
    }


def save_stt_config(stt_cfg: dict) -> None:
    """保存 STT 配置到 JSON 文件"""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    existing = {}
    if _CONFIG_FILE.exists():
        try:
            with open(_CONFIG_FILE, encoding="utf-8") as f:
                existing = json.load(f)
        except (json.JSONDecodeError, OSError):
            pass
    old_key = existing.get("stt", {}).get("api_key", STT_API_KEY)
    new_key = stt_cfg.get("api_key", "")
    if not new_key or "****" in new_key:
        stt_cfg["api_key"] = old_key
    existing["stt"] = stt_cfg
    with open(_CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(existing, f, ensure_ascii=False, indent=2)
    global STT_API_KEY, STT_BASE_URL, STT_MODEL, STT_LANGUAGE
    STT_API_KEY = stt_cfg.get("api_key", STT_API_KEY)
    STT_BASE_URL = stt_cfg.get("base_url", STT_BASE_URL)
    STT_MODEL = stt_cfg.get("model", STT_MODEL)
    STT_LANGUAGE = stt_cfg.get("language", STT_LANGUAGE)


def get_stt_config_safe() -> dict:
    """获取 STT 配置，API Key 脱敏"""
    cfg = load_stt_config()
    key = cfg.get("api_key", "")
    masked = key[:8] + "****" + key[-4:] if len(key) > 12 else ("****" if key else "")
    return {**cfg, "api_key": masked}
