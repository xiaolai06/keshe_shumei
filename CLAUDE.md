# AI 桌宠 Agent (pi-pet-agent)

> 基于 Raspberry Pi 4B 的 AI 桌面宠物智能体。多模态感知 + 三层记忆 + 情绪计算 + Web 控制台。

## 项目概要

这是一个树莓派课程设计项目。桌宠通过硬件传感器感知环境，通过 LLM 推理做出反应，通过 OLED/LED/音响输出表情和语音，通过 Web 页面提供远程交互。

**关键文件：**
- `PRODUCT.md` — 产品定位、用户画像、设计原则（战略层）
- `DESIGN.md` — 完整视觉规范：色板、字体、间距、组件、布局、动效（执行层）
- `docs/design.html` — 项目总设计说明文档（硬件+软件+Web 全覆盖）
- `docs/ui-design-spec.html` — Web UI 详细设计规范（组件级）

## 技术栈

| 层级 | 技术 | 说明 |
|------|------|------|
| Agent | LangGraph | 有向图状态机: Perceive→Recall→Think→Decide→Act→Reflect |
| LLM | DeepSeek API | OpenAI 兼容，国内低延迟 |
| 语音 | Whisper (tiny/base) | 本地 ~75MB，短句 2-5s |
| Web | FastAPI + Uvicorn | 异步 HTTP + WebSocket |
| 前端 | HTML + Tailwind CSS + Chart.js | CDN 引入 |
| 数据库 | SQLite + ChromaDB | 结构化数据 + 向量语义检索 |
| 硬件 | RPi.GPIO / luma.oled / Adafruit | 传感器和执行器驱动 |
| 调度 | APScheduler | 提醒、定期反思、传感器轮询 |

## 项目结构

```
pi-pet-agent/
├── main.py                  # 入口: 启动 Agent + Web + 调度器
├── config.py                # 全局配置
├── requirements.txt
├── PRODUCT.md               # 产品上下文（给 AI 读）
├── DESIGN.md                # 视觉规范（给 AI 读）
├── CLAUDE.md                # 本文件
│
├── agent/                   # AI Agent
│   ├── graph.py             #   LangGraph 状态机
│   ├── state.py             #   PetState 定义
│   ├── prompt.py            #   System Prompt 模板
│   └── nodes/               #   各节点
│       ├── perceive.py      #     感知
│       ├── recall.py        #     记忆检索
│       ├── think.py         #     LLM 推理
│       ├── decide.py        #     决策路由
│       ├── act.py           #     执行
│       └── reflect.py       #     反思
│
├── tools/                   # Agent 工具集
│   ├── reminder_tool.py
│   ├── memory_tool.py
│   ├── oled_tool.py
│   ├── led_tool.py
│   ├── buzzer_tool.py
│   ├── speaker_tool.py
│   └── camera_tool.py
│
├── memory/                  # 记忆系统
│   ├── manager.py           #   统一接口
│   ├── short_term.py
│   ├── long_term.py         #   ChromaDB + SQLite
│   └── schema.sql
│
├── perception/              # 感知层
│   ├── sensors.py           #   DS18B20 + DHT11
│   ├── microphone.py        #   INMP441 I2S
│   ├── camera.py            #   OpenCV
│   └── speech.py            #   Whisper
│
├── hardware/                # 硬件驱动
│   ├── oled.py
│   ├── led.py
│   ├── buzzer.py
│   ├── speaker.py
│   └── expressions/         #   OLED 表情素材
│
├── scheduler/               # 调度器
│   ├── reminder.py
│   └── tasks.py
│
├── web/                     # Web 前端
│   ├── app.py               #   FastAPI 应用
│   ├── routers/
│   │   ├── sensors.py
│   │   ├── memory.py
│   │   ├── reminders.py
│   │   ├── chat.py
│   │   ├── camera.py
│   │   └── evolution.py
│   └── static/
│       ├── index.html        #   主页
│       ├── app.js
│       └── style.css
│
├── data/
│   └── pet.db               # SQLite 数据库
│
└── docs/
    ├── design.html           # 项目设计说明
    └── ui-design-spec.html   # UI 设计规范
```

## Agent 状态机

```
START → Perceive → Recall → Think → Decide → [Act | Tools | Reflect] → END
```

**PetState 字段：**
- `messages`: 对话历史
- `sensor_data`: 传感器快照 (temp, humidity, light, fire)
- `voice_text`: 语音转文字结果
- `image_desc`: 图像描述
- `recalled_memories`: 检索到的记忆
- `mood`: 当前情绪 (happy/curious/sleepy/alert/chatty/calm/lonely)
- `oled_text`: OLED 输出文字
- `oled_expression`: OLED 表情

**工具集：**
`set_reminder`, `search_memory`, `set_oled`, `set_led`, `play_buzzer`, `play_speaker`, `take_photo`, `save_memory`

## 情绪系统

7 种情绪，由 4 个维度加权计算：
- 环境舒适度 (temp/humidity)
- 交互情感 (对话频率/情感倾向)
- 时间因子 (时段/无互动时长)
- 异常事件 (传感器异常/人脸出现)

平滑处理：EMA(α=0.3) + 连续 3 次一致才切换 + 最短 30s 持续。

每种情绪驱动：OLED 表情 + RGB LED 颜色/模式 + 语音语调 + Web 端实时推送。

## 记忆系统

三层架构融合 MemGPT 分层 + 斯坦福 Generative Agents 评分：

1. **工作记忆** (内存): 最近 10 轮对话 + 当前情绪 + 传感器快照
2. **短期记忆** (SQLite): 今日交互摘要，保留 7 天
3. **长期记忆** (SQLite + ChromaDB): 重要事件 + 用户偏好 + 语义检索

检索公式: `score = recency×0.3 + relevance×0.5 + importance×0.2`

## Web 前端

单页应用，5 个 Tab：
1. **AI 对话** — 左侧实时聊天 + 右侧会话历史，SSE 流式回复
2. **摄像头** — MJPEG 实时流 + 拍照分析 + 分析快照
3. **传感器** — 实时数值条 + Chart.js 温度/湿度/情绪趋势图
4. **记忆回顾** — 长期重要记忆 + 每日短期摘要 + 语义搜索
5. **提醒管理** — 提醒列表 + 内联添加表单

前端技术：HTML + Tailwind CSS (CDN) + Chart.js (CDN) + 原生 JS。无需构建工具。

## 硬件模块 (9 个)

| 模块 | 接口 | 功能 |
|------|------|------|
| DS18B20 温度 | 1-Wire (GPIO4) | 精确温度 |
| DHT11 湿度 | GPIO17 | 环境湿度 |
| USB 摄像头 | USB | 人脸识别/场景理解/MJPEG |
| INMP441 ×2 | I2S | 立体声录音→Whisper |
| SSD1306 OLED | I2C (0x3C) | 表情/文字/数据 |
| RGB LED | GPIO PWM | 情绪颜色 |
| 蜂鸣器 | GPIO PWM | 提示音 |
| USB 音响 | USB Audio | TTS 语音播报 |
| MCP3008 ADC | SPI | MQ-135 模拟→数字 |

## 开发约定

### 代码风格
- Python: PEP 8, type hints, 4 空格缩进
- 前端: 系统字体栈, CSS Custom Properties, 无构建工具
- 所有视觉值引用 DESIGN.md 中的令牌，禁止硬编码

### Git 提交格式
```
<type>: <描述>

类型: feat, fix, refactor, docs, test, chore
```

### 数据库
- SQLite 启用 WAL 模式解决并发: `PRAGMA journal_mode=WAL;`
- 所有时间戳使用 `DATETIME DEFAULT CURRENT_TIMESTAMP`

### API 设计
- 统一返回格式: `{"success": bool, "data": ..., "error": ...}`
- 对话接口使用 SSE 流式返回
- 摄像头使用 MJPEG multipart 流

## 开发计划

| 周次 | 任务 |
|------|------|
| 第 1 周 | 硬件驱动 + 基础架构: GPIO/传感器/OLED/LED/蜂鸣器/音响/SQLite |
| 第 2 周 | Agent + 记忆 + 对话: LangGraph 状态机/DeepSeek API/三层记忆/ChromaDB |
| 第 3 周 | 多模态 + Web + 提醒: Whisper 语音/摄像头/MJPEG/FastAPI/全部页面 |
| 第 4 周 | 联调 + 优化 + 文档: 全模块集成/表情制作/性能优化/答辩准备 |

## 风险

| 风险 | 等级 | 对策 |
|------|------|------|
| 树莓派性能 | 中 | Whisper tiny + LLM 走 API |
| LLM API 不可用 | 中 | 降级为关键词匹配回复 |
| I2S 麦克风配置 | 低 | 备用 USB 麦克风 |
| SQLite 并发 | 低 | WAL 模式 |
