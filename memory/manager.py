"""
Memory Manager — 统一记忆接口（SQLite 版本）
三层: Working Memory (内存) → Short-term (SQLite) → Long-term (SQLite)
"""
import json
import logging
from datetime import datetime, timezone, timedelta

from memory.database import get_conn

logger = logging.getLogger("SmartHome")


class MemoryManager:
    """统一记忆管理接口"""

    def store(self, event: str, importance: int | None = None) -> None:
        """存入一条长期记忆"""
        imp = importance if importance is not None else 5
        try:
            with get_conn() as conn:
                conn.execute(
                    "INSERT INTO long_term_memory (category, content, importance) VALUES (?, ?, ?)",
                    ("event", event, imp),
                )
            logger.debug("Stored memory: %s (importance=%d)", event[:40], imp)
        except Exception as e:
            logger.error("Store memory failed: %s", e)

    def recall(self, query: str, top_k: int = 5) -> list:
        """
        检索最相关记忆（关键词匹配 + 重要性排序）。
        三维度评分: recency×0.3 + relevance×0.5 + importance×0.2
        """
        try:
            with get_conn() as conn:
                # 关键词搜索（SQLite LIKE）
                keywords = [kw for kw in query.split() if len(kw) >= 2]
                if not keywords:
                    keywords = [query]

                conditions = " OR ".join(["content LIKE ?"] * len(keywords))
                params = [f"%{kw}%" for kw in keywords]

                rows = conn.execute(
                    f"""SELECT id, content, importance, created_at
                        FROM long_term_memory
                        WHERE {conditions}
                        ORDER BY importance DESC
                        LIMIT ?""",
                    params + [top_k * 3],  # 取多一些再排序
                ).fetchall()

                results = []
                now = datetime.now(timezone.utc)
                for row in rows:
                    content = row["content"]
                    importance = row["importance"] or 5

                    # 重排序：recency + relevance + importance
                    try:
                        created = datetime.fromisoformat(row["created_at"])
                        if created.tzinfo is None:
                            created = created.replace(tzinfo=timezone.utc)
                        age_hours = (now - created).total_seconds() / 3600
                        recency = max(0, 1 - age_hours / (7 * 24))  # 7 天内线性衰减
                    except (ValueError, TypeError):
                        recency = 0.5

                    # 相关性：关键词命中数
                    relevance = sum(1 for kw in keywords if kw in content) / len(keywords)
                    score = recency * 0.3 + relevance * 0.5 + (importance / 10) * 0.2

                    results.append({
                        "content": content,
                        "importance": importance,
                        "score": round(score, 3),
                        "source": "long_term",
                    })

                results.sort(key=lambda x: x["score"], reverse=True)
                return results[:top_k]
        except Exception as e:
            logger.debug("Recall failed: %s", e)
            return []

    def get_recent_context(self, n: int = 10) -> list:
        """获取最近 N 轮对话上下文"""
        try:
            with get_conn() as conn:
                rows = conn.execute(
                    "SELECT user_input, agent_reply, mood, timestamp FROM interactions ORDER BY id DESC LIMIT ?",
                    (n,),
                ).fetchall()
                results = []
                for row in reversed(rows):
                    if row["user_input"]:
                        results.append({
                            "content": f"用户: {row['user_input']}\n小派: {row['agent_reply']}",
                            "importance": 3,
                            "score": 0,
                            "source": "interaction",
                        })
                return results
        except Exception as e:
            logger.debug("Get recent context failed: %s", e)
            return []

    def get_short_term(self, days: int = 7) -> list:
        """获取短期记忆摘要"""
        try:
            with get_conn() as conn:
                rows = conn.execute(
                    "SELECT date, summary, interaction_count, topics FROM short_term_memory ORDER BY date DESC LIMIT ?",
                    (days,),
                ).fetchall()
                return [dict(row) for row in rows]
        except Exception as e:
            logger.debug("Get short-term failed: %s", e)
            return []

    def reflect(self, recent_memories: list) -> None:
        """反思：用 LLM 总结近期记忆，写入长期记忆"""
        if not recent_memories:
            return

        memories_text = "\n".join(f"- {m['content'][:100]}" for m in recent_memories[:20])
        prompt = [
            {"role": "system", "content": "你是小派的记忆系统。请将以下对话记录总结为 1-3 条重要的长期记忆要点，每条一行。只输出要点，不要解释。"},
            {"role": "user", "content": f"近期对话记录：\n{memories_text}"},
        ]

        try:
            from agent.llm_client import get_llm
            llm = get_llm()
            summary = llm.chat(prompt, max_tokens=200)

            # 存入长期记忆
            for line in summary.strip().split("\n"):
                line = line.strip().lstrip("0123456789.-、 ")
                if line and len(line) > 5:
                    self.store(line, importance=7)

            logger.info("Reflect completed: stored summary")
        except Exception as e:
            logger.warning("Reflect failed: %s", e)

    def log_interaction(self, source: str, user_input: str, reply: str, mood: str) -> None:
        """记录一次交互"""
        try:
            with get_conn() as conn:
                conn.execute(
                    "INSERT INTO interactions (source, user_input, agent_reply, mood) VALUES (?, ?, ?, ?)",
                    (source, user_input, reply, mood),
                )
        except Exception as e:
            logger.debug("Log interaction failed: %s", e)
