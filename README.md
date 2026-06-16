# 智居物语 — 项目说明

> 基于 Raspberry Pi 4B 的 AI 桌面宠物智能体
> 多模态感知 + LangGraph Agent + 三层记忆 + Web 控制台

---

## 一、项目简介

智居物语是一个运行在树莓派 4B 上的 AI 桌面宠物。通过传感器感知环境，通过 LLM 推理做出反应，通过 OLED/LED/蜂鸣器/音响输出表情和声音，通过 Web 页面提供远程交互。

**核心能力：**
- 🤖 AI 智能对话（SSE 流式，支持 DeepSeek/OpenAI 等 6 家 LLM）
- 🎤 语音输入（浏览器录音 → 云端 Whisper 识别 → 文字发送）
- 📊 传感器实时监控 + Chart.js 历史趋势图
- 🧠 三层记忆系统（工作/短期/长期，关键词检索+评分排序）
- 🎥 摄像头实时画面（MJPEG）+ AI 场景分析
- 😊 7 种情绪自动推断（关键词+温度）
- 🔔 提醒管理（APScheduler 定时触发）
- ⚙️ LLM/STT 在线配置（Web 页面切换提供商）

---

## 二、技术栈

| 层级 | 技术 | 说明 |
|------|------|------|
| Agent | LangGraph | 状态机：Perceive→Recall→Think→Decide→Act→Reflect |
| LLM | DeepSeek API | OpenAI 兼容，国内低延迟 |
| 语音 | 云端 Whisper API | 浏览器录音上传，云端识别 |
| Web | FastAPI + Uvicorn | 异步 HTTP + SSE 流式 |
| 前端 | HTML + Tailwind CSS + Chart.js | CDN 引入，无需构建 |
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
├──────────────────────────────────────────────────────┤
│           Agent 状态机 (agent/graph.py)               │
│  perceive → recall → think → decide → act/reflect    │
├──────────┬───────────────┬───────────────────────────┤
│ 感知层   │ 记忆层         │ 工具集                    │
│ sensors  │ database      │ reminder / memory          │
│ camera   │ manager       │ oled / led / buzzer        │
│ speech   │ sensor_manager│ speaker / camera           │
├──────────┴───────────────┴───────────────────────────┤
│                SQLite (WAL) + APScheduler             │
└──────────────────────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────┐
│            硬件层 (GPIO / SPI / I2S / USB)            │
│  DS18B20 · DHT11 · 光照 · MQ-135 · MCP3008          │
│  SSD1306 OLED · RGB LED · 蜂鸣器 · 摄像头 · 音响    │
│  INMP441 麦克风 ×2                                    │
└──────────────────────────────────────────────────────┘
```

---

## 四、目录结构

```
pi-pet-agent/
├── config.py              # 全局配置（路径、引脚、LLM/STT）
├── main.py                # 入口：启动 FastAPI
├── hardware_test.py       # ★ 独立硬件测试脚本
├── requirements.txt       # Python 依赖
│
├── agent/                 # AI Agent
│   ├── state.py           #   PetState 定义
│   ├── prompt.py          #   系统提示词（7 种情绪）
│   ├── llm_client.py      #   LLM 客户端（同步+流式）
│   ├── graph.py           #   LangGraph 状态机
│   └── nodes/             #   perceive/recall/think/decide/act/reflect
│
├── memory/                # 记忆系统
│   ├── schema.sql         #   7 张表定义
│   ├── database.py        #   SQLite 连接（WAL）
│   ├── sensor_manager.py  #   传感器数据读写
│   └── manager.py         #   统一记忆接口
│
├── perception/            # 感知层
│   ├── sensors.py         #   DS18B20 + DHT11 + 光照
│   ├── camera.py          #   USB 摄像头
│   └── speech.py          #   云端 Whisper 语音识别
│
├── hardware/              # 硬件驱动
│   ├── oled.py            #   SSD1306 OLED (SPI)
│   ├── led.py             #   RGB LED (GPIO PWM)
│   ├── buzzer.py          #   有源蜂鸣器
│   └── speaker.py         #   USB 音响
│
├── tools/                 # Agent 工具集（7 个）
│   ├── reminder_tool.py   #   提醒 CRUD
│   ├── memory_tool.py     #   记忆存储/搜索
│   ├── oled_tool.py       #   OLED 控制
│   ├── led_tool.py        #   LED 控制
│   ├── buzzer_tool.py     #   蜂鸣器
│   ├── speaker_tool.py    #   TTS 语音
│   └── camera_tool.py     #   拍照+分析
│
├── scheduler/             # 定时任务
│   ├── reminder.py        #   APScheduler 调度器
│   └── tasks.py           #   每日摘要+情绪日志
│
├── web/                   # Web 服务
│   ├── app.py             #   FastAPI 应用（lifespan 管理）
│   ├── routers/           #   7 个 API 路由
│   └── static/            #   前端 SPA
│
├── data/                  # 运行时数据（自动生成）
│   ├── pet.db             #   SQLite 数据库
│   ├── config.json        #   LLM/STT 配置持久化
│   └── logs/              #   日志
│
└── docs/                  # 设计文档
    ├── hardware-wiring-guide.html   # 接线指南
    ├── hardware-test-guide.html     # 测试指南
    ├── design.html                  # 项目设计说明
    └── ui-design-spec.html          # UI 规范
```

---

## 五、硬件接线详解（BCM 编号，无 GPIO 复用）

### 5.1 DS18B20 温度传感器（1-Wire）

| DS18B20 引脚 | 接树莓派 | 说明 |
|-------------|---------|------|
| VCC（红） | 3.3V（物理1） | 供电 |
| GND（黑） | GND（物理6） | 接地 |
| DQ（黄） | GPIO 4（物理7） | 数据线，**必须**接 4.7kΩ 上拉电阻到 3.3V |

### 5.2 DHT11 温湿度传感器（单总线）

| DHT11 引脚 | 接树莓派 | 说明 |
|-----------|---------|------|
| VCC | 3.3V（物理1） | 供电 |
| DATA | GPIO 17（物理11） | 数据线，**必须**接 10kΩ 上拉电阻到 3.3V |
| GND | GND（物理6） | 接地 |

### 5.3 光照传感器（模拟输出 → MCP3008 ADC）

| 光照传感器引脚 | 接树莓派 | 说明 |
|-------------|---------|------|
| VCC | 3.3V（物理1） | 供电 |
| GND | GND（物理6） | 接地 |
| SIG | MCP3008 CH1 | 模拟信号，经 ADC 转换后通过 SPI 读取 |

### 5.4 MQ-135 气体传感器（模拟输出 → MCP3008 ADC）

| MQ-135 引脚 | 接树莓派 | 说明 |
|------------|---------|------|
| VCC | 5V（物理2） | 供电（需 5V，加热丝需要电流） |
| GND | GND（物理6） | 接地 |
| AOUT | MCP3008 CH0 | 模拟输出（气体浓度→电压） |
| DOUT | 不接 | 数字输出，本项目不用 |

### 5.5 MCP3008 ADC 模块（SPI 总线，光照+气体共用）

| MCP3008 引脚 | 接树莓派 | 说明 |
|-------------|---------|------|
| VDD | 3.3V（物理1） | 数字供电 |
| VREF | 3.3V（物理1） | 参考电压（决定 ADC 量程 0~3.3V） |
| AGND | GND（物理6） | 模拟地 |
| DGND | GND（物理6） | 数字地 |
| CLK | GPIO 11（物理23） | SPI 时钟（与 OLED 共用） |
| DOUT | GPIO 9（物理21） | SPI 数据输出（MISO，ADC→树莓派） |
| DIN | GPIO 10（物理19） | SPI 数据输入（MOSI，树莓派→ADC，与 OLED 共用） |
| CS/SHDN | GPIO 7（物理26） | 片选 CE1（OLED 用 CE0，靠 CS 区分） |
| CH0 | MQ-135 AOUT | 通道 0 → 气体浓度 |
| CH1 | 光照传感器 SIG | 通道 1 → 光照强度 |

### 5.6 SSD1306 OLED 显示屏（SPI，7 引脚）

| OLED 引脚 | 接树莓派 | 说明 |
|----------|---------|------|
| VCC | 3.3V（物理1） | 供电（有的模块支持 5V） |
| GND | GND（物理6） | 接地 |
| DIN | GPIO 10（物理19） | SPI 数据输入（MOSI，与 MCP3008 共用总线） |
| CLK | GPIO 11（物理23） | SPI 时钟（SCLK，与 MCP3008 共用总线） |
| CS | GPIO 8（物理24） | 片选 CE0（MCP3008 用 CE1，靠此脚区分） |
| DC | GPIO 13（物理33） | 数据/命令选择（高电平=数据，低电平=命令） |
| RST | GPIO 24（物理18） | 复位（拉低复位，正常工作时拉高） |

### 5.7 RGB LED（共阳极）

| RGB LED 引脚 | 接树莓派 | 说明 |
|------------|---------|------|
| R 红 | GPIO 27（物理13） | 红色通道，**串联 330Ω 限流电阻** |
| G 绿 | GPIO 22（物理15） | 绿色通道，**串联 330Ω 限流电阻** |
| B 蓝 | GPIO 5（物理29） | 蓝色通道，**串联 330Ω 限流电阻** |
| 公共脚（最长） | 3.3V（物理1） | 共阳极，GPIO LOW=亮，HIGH=灭 |

### 5.8 有源蜂鸣器

| 蜂鸣器引脚 | 接树莓派 | 说明 |
|-----------|---------|------|
| 正极（+）/ 红线 | GPIO 12（物理32） | 信号输入，高电平响 |
| 负极（-）/ 黑线 | GND（物理6） | 接地 |

### 5.9 INMP441 I2S 麦克风 ×2（立体声）

| INMP441 引脚 | 接树莓派 | 说明 |
|-------------|---------|------|
| VDD | 3.3V（物理1） | 供电（两个都接） |
| GND | GND（物理6） | 接地（两个都接） |
| SCK | GPIO 18（物理12） | I2S 位时钟 BCLK（两个共用） |
| WS | GPIO 19（物理35） | I2S 字选择 LRCK（两个共用） |
| SD | GPIO 20（物理38） | I2S 数据输出 DIN（两个都接同一脚，左右声道分时） |
| L/R | 麦克风1→GND，麦克风2→3.3V | 决定左/右声道输出 |

### 5.10 USB 设备

| 设备 | 接树莓派 | 说明 |
|------|---------|------|
| USB 摄像头 | 任意 USB 口 | 系统自动识别为 /dev/video0 |
| USB 音响 | 任意 USB 口 | aplay -l 查看设备号 |

### 5.11 GPIO 引脚汇总（18 个，无复用）

| GPIO | 物理引脚 | 分配模块 | 功能 |
|------|---------|---------|------|
| 4 | 7 | DS18B20 | 1-Wire DQ 数据线 |
| 5 | 29 | RGB LED | 蓝色通道（PWM） |
| 7 | 26 | MCP3008 | SPI CE1 片选 |
| 8 | 24 | SSD1306 OLED | SPI CE0 片选 |
| 9 | 21 | MCP3008 | SPI MISO（ADC 数据输出） |
| 10 | 19 | OLED + MCP3008 | SPI MOSI（共享总线） |
| 11 | 23 | OLED + MCP3008 | SPI SCLK（共享总线） |
| 12 | 32 | 有源蜂鸣器 | 信号输入（高电平响） |
| 13 | 33 | SSD1306 OLED | DC 数据/命令选择 |
| 17 | 11 | DHT11 | DATA 数据线 |
| 18 | 12 | INMP441 ×2 | I2S BCLK 位时钟 |
| 19 | 35 | INMP441 ×2 | I2S LRCK 字选择 |
| 20 | 38 | INMP441 ×2 | I2S DIN 数据 |
| 22 | 15 | RGB LED | 绿色通道（PWM） |
| 24 | 18 | SSD1306 OLED | RST 复位 |
| 27 | 13 | RGB LED | 红色通道（PWM） |

> SPI0 总线由 OLED（CE0）和 MCP3008（CE1）共享，同一时刻只能有一个设备通信。
> 详细接线图见 `docs/hardware-wiring-guide.html`

---

## 六、数据库表（SQLite，7 张）

| 表名 | 用途 | 关键字段 |
|------|------|---------|
| sensor_readings | 传感器数据 | temp, humidity, light, comfort |
| interactions | 对话记录 | user_msg, ai_reply, mood |
| short_term_memory | 短期记忆 | content, summary, importance |
| long_term_memory | 长期记忆 | content, importance, category |
| reminders | 提醒 | content, trigger_at, cron_expr, is_active |
| mood_log | 情绪日志 | mood, score, factors |
| evolution_state | 进化状态 | level, exp, personality |

---

## 七、API 端点

| 端点 | 方法 | 功能 |
|------|------|------|
| `/api/chat` | POST | AI 对话 |
| `/api/chat/stream` | POST | SSE 流式对话 |
| `/api/sensors` | GET | 最新传感器数据 |
| `/api/sensors/history` | GET | 传感器历史（1h/6h/24h/7d） |
| `/api/camera/stream` | GET | MJPEG 视频流 |
| `/api/camera/capture` | POST | 拍照 + AI 分析 |
| `/api/memory` | GET | 记忆查询（分页） |
| `/api/memory/search` | GET | 记忆搜索 |
| `/api/reminders` | GET/POST | 提醒列表/创建 |
| `/api/reminders/{id}` | PUT/DELETE | 提醒修改/删除 |
| `/api/status` | GET | 宠物状态（情绪/等级/经验） |
| `/api/evolution` | GET | 性格特质 |
| `/api/settings/llm` | GET/PUT | LLM 配置管理 |
| `/api/settings/llm/models` | GET | 可用模型列表 |
| `/api/settings/llm/test` | POST | 测试 LLM 连接 |
| `/api/settings/stt` | GET/PUT | STT 配置管理 |
| `/api/settings/stt/test` | POST | 测试 STT 连接 |
| `/api/stt/recognize` | POST | 语音识别 |

---

## 八、功能清单与实现状态

| # | 功能 | 状态 | 需要硬件 | 需要网络 |
|---|------|------|---------|---------|
| 1 | AI 智能对话（SSE 流式） | ✅ 可用 | ❌ | ✅ LLM API |
| 2 | 语音输入识别 | ✅ 可用 | ❌ | ✅ STT API |
| 3 | 传感器数据展示 | ✅ 模拟数据 | 接真实传感器后变真实 | ❌ |
| 4 | 传感器历史趋势图 | ✅ 可用 | 同上 | ❌ |
| 5 | 三层记忆系统 | ✅ 可用 | ❌ | ✅ 反思需 LLM |
| 6 | 提醒管理（增删改查+定时触发） | ✅ 可用 | ❌ | ❌ |
| 7 | 宠物状态与进化 | ✅ 可用 | ❌ | ❌ |
| 8 | LLM/STT 在线配置 | ✅ 可用 | ❌ | ❌ |
| 9 | 摄像头实时画面 | ⚠️ 需摄像头 | ✅ USB 摄像头 | ❌ |
| 10 | 拍照 + AI 场景分析 | ⚠️ 需摄像头 | ✅ USB 摄像头 | ✅ LLM API |
| 11 | OLED 表情显示 | ⚠️ 待实现驱动 | ✅ SSD1306 | ❌ |
| 12 | RGB LED 情绪灯光 | ⚠️ 待实现驱动 | ✅ RGB LED | ❌ |
| 13 | 蜂鸣器提示音 | ⚠️ 待实现驱动 | ✅ 蜂鸣器 | ❌ |
| 14 | USB 音响语音播报 | ⚠️ 待实现驱动 | ✅ USB 音响 | ❌ |
| 15 | 实时传感器读取 | ⚠️ 待实现驱动 | ✅ DS18B20+DHT11+光照 | ❌ |

---

## 九、代码模块详解

### 9.1 Agent 状态机（agent/）

```
START → Perceive → Recall → Think → Decide → Act/Reflect → END
```

| 节点 | 文件 | 功能 |
|------|------|------|
| perceive | perceive.py | 读传感器（硬件/mock/传入三级回退） |
| recall | recall.py | 提取用户消息，检索相关记忆 |
| think | think.py | 构建提示词 + 调用 LLM 生成回复 |
| decide | decide.py | 每 20 轮路由到 reflect，否则 act |
| act | act.py | 推断情绪（关键词+温度），记录交互 |
| reflect | reflect.py | LLM 总结近期交互存入长期记忆 |

LLM 客户端（llm_client.py）：支持同步 `chat()` + 异步流式 `chat_stream()`，6 家提供商预设。

### 9.2 记忆系统（memory/）

| 层级 | 存储 | 保留 | 内容 |
|------|------|------|------|
| 工作记忆 | 内存 | 当前会话 | 最近 10 轮对话 + 情绪 + 传感器 |
| 短期记忆 | SQLite | 7 天 | 每日交互摘要 |
| 长期记忆 | SQLite | 永久 | 重要事件 + 用户偏好 |

检索公式：`score = 时效性×0.3 + 相关性×0.5 + 重要性×0.2`

### 9.3 语音识别（perception/speech.py）

```
浏览器录音 → POST /api/stt/recognize → 云端 Whisper API → 返回文字
```

- 支持 webm/wav/mp3/ogg 格式
- HTTP 双保险：httpx 优先，requests 回退
- 配置持久化到 data/config.json

### 9.4 Web 前端（web/static/）

单页应用，5 个 Tab：

| Tab | 功能 |
|-----|------|
| AI 对话 | 聊天 + SSE 流式回复 + 语音输入 |
| 摄像头 | MJPEG 实时流 + 拍照分析 |
| 传感器 | 实时数值 + Chart.js 趋势图 |
| 记忆回顾 | 长期记忆 + 短期摘要 + 搜索 |
| 提醒管理 | 提醒 CRUD + 定时触发 |

### 9.5 工具集（tools/）

Agent 可调用 7 个工具：`set_reminder` / `search_memory` / `set_oled` / `set_led` / `play_buzzer` / `play_speaker` / `take_photo`

### 9.6 定时任务（scheduler/）

- `reminder.py` — APScheduler 调度器（一次/周期/间隔提醒）
- `tasks.py` — 每日摘要 + 情绪日志

---

## 十、启动与测试

### 启动

```bash
# 安装依赖
pip install fastapi uvicorn langgraph openai httpx apscheduler

# 配置 API Key
export DEEPSEEK_API_KEY="sk-your-key"

# 启动
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
python hardware_test.py dht11      # 温湿度传感器
python hardware_test.py light      # 光照传感器（MCP3008）
python hardware_test.py mq135      # 气体传感器（MCP3008）
python hardware_test.py oled       # OLED 显示屏
python hardware_test.py led        # RGB LED
python hardware_test.py buzzer     # 蜂鸣器
python hardware_test.py camera     # USB 摄像头
python hardware_test.py speaker    # USB 音响
python hardware_test.py mic        # I2S 麦克风
```

---

## 十一、依赖安装

```bash
# 核心
pip install fastapi uvicorn langgraph openai httpx apscheduler

# 摄像头（可选）
pip install opencv-python

# 硬件（仅树莓派）
pip install RPi.GPIO luma.oled pillow adafruit-circuitpython-dht spidev edge-tts
sudo apt install mpg123
```

---

## 十二、已知问题

| # | 问题 | 修复建议 |
|---|------|---------|
| 1 | `web/routers/status.py` 用 `eval()` 解析 DB 内容 | 改为 `json.loads()` |
| 2 | 流式对话硬编码 `mood="happy"` | 查询实际情绪状态 |
| 3 | 6 个硬件驱动文件为 stub/TODO | 需补充 RPi.GPIO / luma.oled 实现 |
