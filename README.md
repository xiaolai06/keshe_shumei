# 智居物语 — 项目说明

> 基于 Raspberry Pi 4B 的 AI 桌面宠物智能体
> 多模态感知 + LangGraph Agent + 三层记忆 + 时间感知 + Web 控制台

---

## 一、项目简介

智居物语是一个运行在树莓派 4B 上的 AI 桌面宠物。通过传感器感知环境，通过 LLM 推理做出反应，通过 RGB OLED 显示屏/蜂鸣器/USB 音响输出表情和声音，通过 Web 页面提供远程交互。

**核心能力：**
- 🤖 AI 智能对话（SSE 流式，支持 DeepSeek/OpenAI 等 6 家 LLM）
- 🕐 时间感知与环境分析（时段问候 + 传感器数据智能解读，不只报数字）
- 🎤 语音输入（INMP441 I2S 麦克风 → 云端 Whisper 识别 → 文字发送）
- 📊 传感器实时监控 + Chart.js 历史趋势图
- 🧠 三层记忆系统（工作/短期/长期，关键词检索+评分排序）
- 🎥 摄像头实时画面（MJPEG）+ AI 场景分析
- 😊 7 种情绪自动推断（关键词+温度）
- 🎨 SSD1351 RGB 彩色 OLED 表情显示（128×128）
- 🔔 提醒管理（APScheduler 定时触发）
- ⚙️ LLM/STT 在线配置（Web 页面切换提供商）
- 🔒 线程安全单例、上传大小限制、GPIO 资源正确释放

---

## 二、技术栈

| 层级 | 技术 | 说明 |
|------|------|------|
| Agent | LangGraph | 状态机：Perceive→Recall→Think→Decide→Act→Reflect |
| LLM | DeepSeek API | OpenAI 兼容接口，国内低延迟 |
| 语音识别 | 云端 Whisper API | INMP441 I2S 麦克风录音，云端识别 |
| 语音合成 | edge-tts | 微软 TTS → MP3 → mpg123 播放 |
| Web | FastAPI + Uvicorn | 异步 HTTP + SSE 流式 + MJPEG |
| 前端 | HTML + CSS + Chart.js | CDN 引入，无需构建 |
| 数据库 | SQLite | WAL 模式，7 张表 |
| 硬件 | RPi.GPIO / luma.oled / OpenCV | 传感器和执行器 |
| 调度 | APScheduler | 定时提醒 |

---

## 三、系统架构

```
┌─────────────────────────────────────────────────────┐
│                  浏览器（SPA）                        │
│     index.html + app.js + style.css                  │
│     5 Tab: 对话 | 摄像头 | 传感器 | 记忆 | 提醒       │
└────────────────────┬────────────────────────────────┘
                     │ HTTP / SSE / MJPEG
┌────────────────────▼────────────────────────────────┐
│              FastAPI (web/app.py)                     │
│  /api/chat  /api/sensors  /api/camera                │
│  /api/memory /api/reminders /api/status              │
│  /api/settings/llm  /api/settings/stt                │
│  /api/voice/*  /api/stt/recognize                    │
├──────────────────────────────────────────────────────┤
│           Agent 状态机 (agent/graph.py)               │
│  perceive → recall → think → decide → act/reflect    │
│  ┌────────────────────────────────────────────┐      │
│  │ System Prompt 动态构建：                      │      │
│  │  · 情绪映射 · 时间感知 · 环境分析 · 记忆注入  │      │
│  └────────────────────────────────────────────┘      │
├──────────┬───────────────┬───────────────────────────┤
│ 感知层   │ 记忆层         │ 工具集                    │
│ sensors  │ database      │ reminder / memory          │
│ camera   │ manager       │ oled / buzzer              │
│ speech   │ sensor_manager│ speaker / camera           │
│ listener │               │                            │
├──────────┴───────────────┴───────────────────────────┤
│        SQLite (WAL) + APScheduler + .gitignore       │
└──────────────────────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────┐
│            硬件层 (GPIO / SPI / I2S / USB)            │
│  DS18B20 · DHT22 · 光敏传感器(数字输出)              │
│  SSD1351 RGB OLED · 有源蜂鸣器 · USB 摄像头          │
│  INMP441 I2S 麦克风 · Waveshare USB 音响            │
└──────────────────────────────────────────────────────┘
```

---

## 四、目录结构

```
pi-pet-agent-final/
├── config.py              # 全局配置（路径、引脚、LLM/STT）
├── main.py                # 入口：启动 FastAPI
├── hardware_test.py       # ★ 独立硬件测试脚本（9 个模块）
├── requirements.txt       # Python 依赖
├── .gitignore             # 敏感文件屏蔽（data/config.json 等）
│
├── agent/                 # AI Agent
│   ├── state.py           #   PetState 定义
│   ├── prompt.py          #   系统提示词（时间感知+环境分析+情绪）
│   ├── llm_client.py      #   LLM 客户端（同步+流式，线程安全单例）
│   ├── graph.py           #   LangGraph 状态机（线程安全单例）
│   └── nodes/             #   perceive/recall/think/decide/act/reflect
│
├── memory/                # 记忆系统
│   ├── schema.sql         #   7 张表定义
│   ├── database.py        #   SQLite 连接（WAL）
│   ├── sensor_manager.py  #   传感器数据读写
│   └── manager.py         #   统一记忆接口（关键词检索+评分排序）
│
├── perception/            # 感知层
│   ├── sensors.py         #   DS18B20 + DHT22 + 光敏(数字)，GPIO 一次性初始化
│   ├── camera.py          #   USB 摄像头
│   ├── speech.py          #   云端 Whisper 语音识别（httpx + requests 双保险）
│   ├── microphone.py      #   INMP441 I2S 麦克风驱动（arecord）
│   └── listener.py        #   VAD 持续监听 + STT + Agent 自动触发
│
├── hardware/              # 硬件驱动（全部单例模式 + 线程锁）
│   ├── oled.py            #   SSD1351 RGB OLED (SPI, 128×128)
│   ├── buzzer.py          #   有源蜂鸣器模块（固定频率，duration 控制）
│   ├── speaker.py         #   Waveshare USB 音响（asyncio.Lock 串行播放）
│   └── led.py             #   RGB LED 兼容桩（未配置硬件）
│
├── tools/                 # Agent 工具集
│   ├── reminder_tool.py   #   提醒 CRUD
│   ├── memory_tool.py     #   记忆存储/搜索
│   ├── oled_tool.py       #   OLED 控制
│   ├── buzzer_tool.py     #   蜂鸣器（使用 get_buzzer() 单例）
│   ├── speaker_tool.py    #   TTS 语音
│   ├── camera_tool.py     #   拍照+分析
│   └── led_tool.py        #   LED 兼容桩（未配置硬件）
│
├── scheduler/             # 定时任务
│   ├── reminder.py        #   APScheduler 调度器（一次/周期/间隔）
│   └── tasks.py           #   每日摘要+情绪日志
│
├── web/                   # Web 服务
│   ├── app.py             #   FastAPI 应用（lifespan 管理 + GPIO 清理）
│   ├── routers/           #   8 个 API 路由模块
│   └── static/            #   前端 SPA
│
├── data/                  # 运行时数据（.gitignore 屏蔽）
│   ├── pet.db             #   SQLite 数据库
│   ├── config.json        #   LLM/STT 配置持久化（含 API Key）
│   └── logs/              #   日志
│
└── docs/                  # 设计文档
    ├── hardware-wiring-guide.html   # 接线指南
    ├── hardware-test-guide.html     # 测试指南
    ├── design.html                  # 项目设计说明
    ├── code-explained.html          # 代码详解
    ├── dev-guide.html               # 开发指南
    ├── ui-design-spec.html          # UI 规范
    └── 元器件说明.md                 # 元器件清单说明
```

---

## 五、元器件清单

| # | 元器件 | 型号/规格 | 数量 | 用途 |
|---|--------|----------|------|------|
| 1 | 温度传感器 | DS18B20 防水型 (10KΩ上拉) | 1 | 1-Wire 环境温度 |
| 2 | 温湿度传感器 | DHT22 (蓝色滤网盖) | 1 | 温度+湿度双参数 |
| 3 | 光照传感器 | 光敏电阻模块 (LM393比较器) | 1 | 环境光数字量检测 |
| 4 | RGB OLED | SSD1351 1.5寸 128×128 彩色 | 1 | 表情/文字/数据显示 |
| 5 | 蜂鸣器模块 | 有源蜂鸣器 (3脚模块) | 1 | 提示音/报警 |
| 6 | USB 声卡音响 | Waveshare USB TO AUDIO + 喇叭×2 | 1套 | TTS 语音输出 |
| 7 | I2S 麦克风 | INMP441 MEMS 数字麦克风 | 1 | 语音输入 |
| 8 | USB 摄像头 | 通用 USB 摄像头 | 1 | 实时画面/拍照分析 |
| 9 | 主控板 | Raspberry Pi 4B | 1 | 系统主控 |

---

## 六、硬件接线详解（BCM 编号，无 GPIO 复用）

### 6.1 DS18B20 温度传感器（1-Wire）

| DS18B20 引脚 | 接树莓派 | 说明 |
|-------------|---------|------|
| VCC（红） | 3.3V（物理1） | 供电 |
| GND（黑） | GND（物理6） | 接地 |
| DQ（黄） | GPIO 4（物理7） | 数据线，**必须**接 10KΩ 上拉电阻到 3.3V |

### 6.2 DHT22 温湿度传感器（单总线）

| DHT22 引脚 | 接树莓派 | 说明 |
|-----------|---------|------|
| VCC | 3.3V（物理1） | 供电 |
| DATA | GPIO 17（物理11） | 数据线，需要 10KΩ 上拉电阻到 3.3V（部分模块已集成） |
| GND | GND（物理6） | 接地 |

### 6.3 光照传感器模块（数字输出，LM393 比较器）

| 光照传感器引脚 | 接树莓派 | 说明 |
|-------------|---------|------|
| VCC | 3.3V（物理1） | 供电 |
| GND | GND（物理6） | 接地 |
| SIG | GPIO 27（物理13） | 数字信号输出（HIGH=光照充足，LOW=光照不足） |

> 模块上通常有电位器可调节灵敏度阈值。输出为比较器数字量，非模拟量。

### 6.4 SSD1351 RGB OLED 显示屏（SPI，7 引脚，128×128 彩色）

| OLED 引脚 | 接树莓派 | 说明 |
|----------|---------|------|
| VCC | 3.3V（物理1） | 供电 |
| GND | GND（物理6） | 接地 |
| DIN | GPIO 10（物理19） | SPI 数据输入（MOSI） |
| CLK | GPIO 11（物理23） | SPI 时钟（SCLK） |
| CS | GPIO 8（物理24） | 片选 CE0 |
| DC | GPIO 13（物理33） | 数据/命令选择（高电平=数据，低电平=命令） |
| RST | GPIO 24（物理18） | 复位（拉低复位，正常工作时拉高） |

> SPI0 总线由 SSD1351 OLED 独占使用。

### 6.5 有源蜂鸣器模块（3 脚）

| 蜂鸣器引脚 | 接树莓派 | 说明 |
|-----------|---------|------|
| VCC | 3.3V（物理1） | 供电 |
| GND | GND（物理6） | 接地 |
| IN | GPIO 12（物理32） | 信号输入（高电平响，低电平停） |

> 有源蜂鸣器只能在固定频率发声，代码中通过控制响/停时长来组合不同音效。

### 6.6 INMP441 I2S 麦克风

| INMP441 引脚 | 接树莓派 | 说明 |
|-------------|---------|------|
| VDD | 3.3V（物理1） | 供电 |
| GND | GND（物理6） | 接地 |
| SCK | GPIO 18（物理12） | I2S 位时钟 BCLK |
| WS | GPIO 19（物理35） | I2S 字选择 LRCK |
| SD | GPIO 20（物理38） | I2S 数据输出 DIN |
| L/R | GND | 选择左声道输出（接 GND = 左声道） |

> 需在 /boot/config.txt 中添加 `dtoverlay=i2s-mmic` 启用 I2S 驱动。

### 6.7 USB 设备

| 设备 | 接树莓派 | 说明 |
|------|---------|------|
| USB 摄像头 | 任意 USB 口 | 系统自动识别为 /dev/video0 |
| Waveshare USB 音响 | 任意 USB 口 | aplay -l 查看设备号 |

### 6.8 GPIO 引脚汇总（12 个 GPIO，无复用）

| GPIO | 物理引脚 | 分配模块 | 功能 |
|------|---------|---------|------|
| 4 | 7 | DS18B20 | 1-Wire DQ 数据线 |
| 8 | 24 | SSD1351 OLED | SPI CE0 片选 |
| 10 | 19 | SSD1351 OLED | SPI MOSI 数据输入 |
| 11 | 23 | SSD1351 OLED | SPI SCLK 时钟 |
| 12 | 32 | 有源蜂鸣器 | IN 信号输入（高电平响） |
| 13 | 33 | SSD1351 OLED | DC 数据/命令选择 |
| 17 | 11 | DHT22 | DATA 数据线 |
| 18 | 12 | INMP441 | I2S BCLK 位时钟 |
| 19 | 35 | INMP441 | I2S LRCK 字选择 |
| 20 | 38 | INMP441 | I2S DIN 数据 |
| 24 | 18 | SSD1351 OLED | RST 复位 |
| 27 | 13 | 光照传感器 | SIG 数字信号输出 |

> SPI0 总线由 SSD1351 OLED 独占使用，不与 ADC 共享。
> 详细接线图见 `docs/hardware-wiring-guide.html`

---

## 七、数据库表（SQLite，7 张）

| 表名 | 用途 | 关键字段 |
|------|------|---------|
| sensor_readings | 传感器数据 | temp, humidity, light_level |
| interactions | 对话记录 | source, user_input, agent_reply, mood |
| short_term_memory | 短期记忆 | content, summary, importance |
| long_term_memory | 长期记忆 | content, importance, category |
| reminders | 提醒 | content, trigger_at, cron_expr, is_active |
| mood_log | 情绪日志 | mood, score, factors |
| evolution_state | 进化状态 | level, exp, personality |

---

## 八、API 端点

| 端点 | 方法 | 功能 |
|------|------|------|
| `/api/chat` | POST | AI 对话（走 Agent 状态机） |
| `/api/chat/stream` | POST | SSE 流式对话（记忆检索+情绪推断+环境分析+OLED更新+TTS） |
| `/api/sensors` | GET | 最新传感器数据 |
| `/api/sensors/history` | GET | 传感器历史（1h/6h/24h/7d） |
| `/api/camera/stream` | GET | MJPEG 视频流（asyncio.to_thread 非阻塞） |
| `/api/camera/capture` | POST | 拍照 + AI 分析 |
| `/api/memory` | GET | 记忆查询（分页） |
| `/api/memory/search` | GET | 记忆搜索 |
| `/api/reminders` | GET/POST | 提醒列表/创建 |
| `/api/reminders/{id}` | PUT/DELETE | 提醒修改/删除 |
| `/api/status` | GET | 宠物状态（情绪/等级/经验） |
| `/api/evolution` | GET | 性格特质 |
| `/api/evolution/history` | GET | 情绪变化历史 |
| `/api/settings/llm` | GET/PUT | LLM 配置管理 |
| `/api/settings/llm/models` | GET | 可用模型列表 |
| `/api/settings/llm/test` | POST | 测试 LLM 连接 |
| `/api/settings/stt` | GET/PUT | STT 配置管理 |
| `/api/settings/stt/test` | POST | 测试 STT 连接 |
| `/api/stt/recognize` | POST | 语音识别（≤10MB） |
| `/api/voice/status` | GET | 语音监听状态 |
| `/api/voice/start` | POST | 启动语音监听 |
| `/api/voice/stop` | POST | 停止语音监听 |
| `/api/voice/trigger` | POST | 远程文字触发 Agent |
| `/api/voice/upload` | POST | 上传音频识别（≤10MB） |

---

## 九、功能清单与实现状态

| # | 功能 | 状态 | 需要硬件 | 需要网络 |
|---|------|------|---------|---------|
| 1 | AI 智能对话（SSE 流式） | ✅ 可用 | ❌ | ✅ LLM API |
| 2 | 时间感知与环境分析 | ✅ 可用 | ✅ 传感器 | ❌ |
| 3 | 语音输入识别 | ✅ 可用 | ✅ INMP441 麦克风 | ✅ STT API |
| 4 | DS18B20 温度传感 | ✅ 可用 | ✅ DS18B20 | ❌ |
| 5 | DHT22 温湿度传感 | ✅ 可用 | ✅ DHT22 | ❌ |
| 6 | 光敏传感器（数字输出） | ✅ 可用 | ✅ 光敏模块 | ❌ |
| 7 | 传感器历史趋势图 | ✅ 可用 | 同上 | ❌ |
| 8 | 三层记忆系统 | ✅ 可用 | ❌ | ✅ 反思需 LLM |
| 9 | 提醒管理（增删改查+定时触发） | ✅ 可用 | ❌ | ❌ |
| 10 | 宠物状态与进化 | ✅ 可用 | ❌ | ❌ |
| 11 | LLM/STT 在线配置 | ✅ 可用 | ❌ | ❌ |
| 12 | 摄像头实时画面 | ✅ 可用 | ✅ USB 摄像头 | ❌ |
| 13 | 拍照 + AI 场景分析 | ✅ 可用 | ✅ USB 摄像头 | ✅ LLM API |
| 14 | SSD1351 RGB OLED 彩色表情 | ✅ 可用 | ✅ SSD1351 OLED | ❌ |
| 15 | 蜂鸣器提示音/报警 | ✅ 可用 | ✅ 蜂鸣器模块 | ❌ |
| 16 | USB 音响 TTS 语音播报 | ✅ 可用 | ✅ USB 音响 | ❌ |

---

## 十、代码模块详解

### 10.1 Agent 状态机（agent/）

```
START → Perceive → Recall → Think → Decide → Act/Reflect → END
```

| 节点 | 文件 | 功能 |
|------|------|------|
| perceive | perceive.py | 读传感器（硬件/mock/传入三级回退），注入 datetime + hour |
| recall | recall.py | 提取用户消息，MemoryManager 关键词检索 + 最近上下文（已修复变量未绑定） |
| think | think.py | 构建提示词 + 调用 LLM 生成回复 |
| decide | decide.py | 每 N 轮路由到 reflect，否则 act |
| act | act.py | 推断情绪（关键词+温度），记录交互（自动识别来源 web/voice），控制 OLED+蜂鸣器 |
| reflect | reflect.py | LLM 总结近期交互存入长期记忆 |

**System Prompt 动态构建（prompt.py）：**

系统提示词每次对话前动态生成，包含：

1. **情绪映射** — 7 种情绪对应不同语调（happy/curious/sleepy/alert/chatty/calm/lonely）
2. **时间感知** — 获取当前时间和星期，自动判断时段（清晨/上午/中午/下午/晚上/深夜/凌晨），生成对应问候建议
3. **环境分析** — 对传感器原始数据进行智能解读：温度分 6 档（很热/闷热/偏暖/舒适/凉/冷），湿度分 5 档（潮湿/偏闷/舒适/偏干/干燥），光照判断亮/暗，给出综合舒适度评估和生活建议
4. **记忆注入** — 将检索到的相关记忆作为上下文注入

LLM 客户端（llm_client.py）：支持同步 `chat()` + 异步流式 `chat_stream()`，6 家提供商预设。全局单例使用 `threading.Lock` 保护。

### 10.2 记忆系统（memory/）

| 层级 | 存储 | 保留 | 内容 |
|------|------|------|------|
| 工作记忆 | 内存 | 当前会话 | 最近 10 轮对话 + 情绪 + 传感器 |
| 短期记忆 | SQLite | 7 天 | 每日交互摘要 |
| 长期记忆 | SQLite | 永久 | 重要事件 + 用户偏好 |

检索公式：`score = 时效性×0.3 + 相关性×0.5 + 重要性×0.2`

### 10.3 语音识别（perception/）

```
INMP441 麦克风 → arecord → VAD 能量检测 → 云端 Whisper API → 文字
浏览器录音 → POST /api/stt/recognize → 云端 Whisper API → 返回文字
上传音频   → POST /api/voice/upload  → 云端 Whisper API → 文字送 Agent
```

- 支持 webm/wav/mp3/ogg 格式
- HTTP 双保险：httpx 优先，requests 回退
- 配置持久化到 data/config.json（API Key 脱敏显示）
- 上传接口限制 10MB 防止内存耗尽

### 10.4 硬件驱动层（hardware/）

所有硬件驱动采用单例模式 + 线程安全锁：

| 驱动 | 单例获取 | 线程安全 | 特殊说明 |
|------|---------|---------|---------|
| OLED | `get_oled()` | ✅ 双检锁 | SPI 独占 SPI0 总线 |
| 蜂鸣器 | `get_buzzer()` | ✅ 双检锁 | 有源蜂鸣器，固定频率，duration 控制 |
| 音响 | `get_speaker()` | ✅ 双检锁 | asyncio.Lock 串行播放，防重叠 |
| 传感器 | `SensorReader` | ✅ GPIO 一次初始化 | `GPIO.setmode` 仅调用一次 |
| LED | `get_led()` | — | 兼容桩，无实际硬件 |

应用关闭时通过 lifespan shutdown 调用 `GPIO.cleanup()` 正确释放所有 GPIO 资源。

### 10.5 Web 前端（web/static/）

单页应用，5 个 Tab：

| Tab | 功能 |
|-----|------|
| AI 对话 | 聊天 + SSE 流式回复 + 语音输入 |
| 摄像头 | MJPEG 实时流 + 拍照分析 |
| 传感器 | 实时数值 + Chart.js 趋势图 |
| 记忆回顾 | 长期记忆 + 短期摘要 + 搜索 |
| 提醒管理 | 提醒 CRUD + 定时触发 |

### 10.6 工具集（tools/）

Agent 可调用工具：`set_reminder` / `search_memory` / `set_oled` / `play_buzzer` / `play_speaker` / `take_photo`

### 10.7 定时任务（scheduler/）

- `reminder.py` — APScheduler 调度器（一次/周期/间隔提醒）
- `tasks.py` — 每日摘要 + 情绪日志

---

## 十一、启动与测试

### 系统前置配置

```bash
# 启用 1-Wire（DS18B20 温度传感器）
echo "dtoverlay=w1-gpio" | sudo tee -a /boot/config.txt

# 启用 I2S（INMP441 麦克风）
echo "dtoverlay=i2s-mmic" | sudo tee -a /boot/config.txt

# 启用 SPI（OLED 显示屏）
sudo raspi-config  # Interface Options → SPI → Enable

# 安装系统依赖
sudo apt install mpg123 alsa-utils

# 重启生效
sudo reboot
```

### 安装依赖

```bash
# 核心
pip install fastapi uvicorn langgraph openai httpx apscheduler

# 摄像头（可选）
pip install opencv-python

# 硬件（仅树莓派）
pip install RPi.GPIO luma.oled pillow adafruit-circuitpython-dht edge-tts
```

或一次性安装：`pip install -r requirements.txt`

### 配置 API Key

```bash
export DEEPSEEK_API_KEY="sk-your-key"
```

或在 Web 设置页面中配置。

> **安全提示：** `data/config.json` 已加入 `.gitignore`，不会被提交到版本控制。首次启动前请确保 API Key 不在版本控制中暴露。

### 启动

```bash
python main.py

# 浏览器访问
# http://localhost:8000
```

### 硬件测试

```bash
# 测试全部硬件
python hardware_test.py

# 测试指定模块
python hardware_test.py ds18b20    # 温度传感器
python hardware_test.py dht22      # 温湿度传感器
python hardware_test.py light      # 光照传感器
python hardware_test.py oled       # SSD1351 OLED 显示屏
python hardware_test.py buzzer     # 蜂鸣器模块
python hardware_test.py camera     # USB 摄像头
python hardware_test.py speaker    # USB 音响
python hardware_test.py mic        # I2S 麦克风
python hardware_test.py voice      # 语音识别完整链路
```

---

## 十二、代码质量保障

### 已修复的关键问题

| 类别 | 问题 | 修复措施 |
|------|------|---------|
| 安全 | API Key 明文存储在 config.json | 创建 `.gitignore` 屏蔽敏感文件 |
| 崩溃 | `status.py` 缺少 `import json` 导致 NameError | 补上 import |
| 崩溃 | `recall_node` 中 `mm` 变量可能未绑定 | MemoryManager 初始化提前，加 None 守卫 |
| 资源 | 生产代码从不调用 `GPIO.cleanup()` | lifespan 关闭时释放 GPIO |
| 安全 | 音频上传无大小限制 | voice/settings 端点限制 10MB |
| 冲突 | `GPIO.setmode()` 每次读传感器都调用 | 改为一次性 `_ensure_gpio()` 初始化 |
| 误导 | 有源蜂鸣器 `beep(freq)` 参数无效 | 移除 freq，简化为 `beep(duration)` |
| 竞态 | `get_agent()` / `get_llm()` 单例无线程安全 | 加 `threading.Lock` 双检锁 |
| 重叠 | Speaker TTS 并发播放音频重叠 | `asyncio.Lock` 串行化播放 |
| 阻塞 | 摄像头 MJPEG 阻塞事件循环 | `asyncio.to_thread` 包装阻塞调用 |
| 错误 | `act_node` 交互来源硬编码 "web" | 从 state 推断（voice/web） |
| 功能 | 流式对话绕过 Agent 核心功能 | 补充记忆检索+情绪推断+环境分析+OLED+TTS |

### 设计决策说明

- **有源蜂鸣器**：有源蜂鸣器内置振荡器，只能开/关，无法变频。代码通过不同时长组合实现不同音效（短响、长响、节奏响等）。如需变频音效需换用无源蜂鸣器 + PWM 驱动。
- **GPIO 一次性初始化**：`GPIO.setmode()` 是进程全局设置，多处调用可能导致冲突。传感器模块改为首次调用时初始化一次。
- **TTS 串行播放**：多个异步任务可能同时触发 TTS，通过 `asyncio.Lock` 确保同一时刻只有一段音频在播放。
- **流式对话增强**：SSE 流式端点虽然绕过 LangGraph 状态机（为保持低延迟），但手动补充了记忆检索、情绪推断、OLED 更新和 TTS 播报等核心功能，并通过 `[META]` SSE 事件将情绪推送前端。

---

## 十三、已知待改进

| # | 问题 | 说明 |
|---|------|------|
| 1 | `reflect` 分支实际不触发 | 每次请求都是全新 state，interaction_count 始终为 1，需持久化计数器 |
| 2 | 前端 UI 为静态 Mock | 图表、记忆、提醒等 Tab 尚未对接 API |
| 3 | API 无认证 | 绑定 0.0.0.0:8000，局域网内无访问控制 |
| 4 | OLED 显示无并发锁 | listener 线程和 scheduler 可能同时操作 SPI |
| 5 | 麦克风重启恢复循环 | arecord 进程异常退出后 VAD 循环无法自动恢复 |
| 6 | `camera.py` 为死代码 | 实际由 `camera_tool.py` 直接调用 cv2 |
