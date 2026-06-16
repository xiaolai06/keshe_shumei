-- AI 桌宠 Agent — SQLite 数据库 Schema
-- 启用 WAL 模式
PRAGMA journal_mode=WAL;

-- 传感器数据（每 10 秒一条）
CREATE TABLE IF NOT EXISTS sensor_readings (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp   DATETIME DEFAULT CURRENT_TIMESTAMP,
    temperature REAL,
    humidity    REAL,
    light_level REAL
);

-- 交互记录
CREATE TABLE IF NOT EXISTS interactions (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp   DATETIME DEFAULT CURRENT_TIMESTAMP,
    source      TEXT,          -- 'voice' / 'web' / 'system'
    user_input  TEXT,
    agent_reply TEXT,
    mood        TEXT,
    tools_used  TEXT           -- JSON array
);

-- 短期记忆（每日摘要）
CREATE TABLE IF NOT EXISTS short_term_memory (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    date        DATE,
    summary     TEXT,
    interaction_count INTEGER,
    temp_range  TEXT,          -- "23~26°C"
    topics      TEXT,          -- "笑话、日常"
    created_at  DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 长期记忆
CREATE TABLE IF NOT EXISTS long_term_memory (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    category      TEXT,        -- 'event' / 'preference' / 'reflection'
    content       TEXT,
    importance    REAL DEFAULT 5,
    embedding_id  TEXT,        -- ChromaDB 向量 ID
    created_at    DATETIME DEFAULT CURRENT_TIMESTAMP,
    last_recalled DATETIME
);

-- 提醒规则
CREATE TABLE IF NOT EXISTS reminders (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    content    TEXT NOT NULL,
    type       TEXT DEFAULT 'once',   -- 'once' / 'cron' / 'condition'
    trigger_at DATETIME,
    cron_expr  TEXT,
    condition  TEXT,                  -- JSON
    is_active  BOOLEAN DEFAULT 1,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 情绪日志
CREATE TABLE IF NOT EXISTS mood_log (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    mood      TEXT NOT NULL,          -- happy/curious/sleepy/alert/chatty/calm/lonely
    score     REAL,                   -- 0~1
    factors   TEXT                    -- JSON: {env, interact, time, event}
);

-- 进化状态
CREATE TABLE IF NOT EXISTS evolution_state (
    id          INTEGER PRIMARY KEY DEFAULT 1,
    name        TEXT DEFAULT '小派',
    mood        TEXT DEFAULT 'happy',
    level       INTEGER DEFAULT 1,
    exp         INTEGER DEFAULT 0,
    personality TEXT,                  -- JSON
    updated     DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 初始化进化状态
INSERT OR IGNORE INTO evolution_state (id, name, mood, level, exp)
VALUES (1, '智居物语', 'happy', 1, 0);
