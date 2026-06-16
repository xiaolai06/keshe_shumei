"""
AI Agent — LangGraph 状态机
节点: Perceive → Recall → Think → Decide → [Act | Reflect] → END
"""
import logging
import threading
from langgraph.graph import StateGraph, END
from agent.state import PetState
from agent.nodes.perceive import perceive_node
from agent.nodes.recall import recall_node
from agent.nodes.think import think_node
from agent.nodes.decide import decide_node, route_decision
from agent.nodes.act import act_node
from agent.nodes.reflect import reflect_node

logger = logging.getLogger("SmartHome")


def build_graph():
    """构建并编译 LangGraph 状态机"""
    graph = StateGraph(PetState)

    # 添加节点
    graph.add_node("perceive", perceive_node)
    graph.add_node("recall", recall_node)
    graph.add_node("think", think_node)
    graph.add_node("decide", decide_node)
    graph.add_node("act", act_node)
    graph.add_node("reflect", reflect_node)

    # 定义边
    graph.set_entry_point("perceive")
    graph.add_edge("perceive", "recall")
    graph.add_edge("recall", "think")
    graph.add_edge("think", "decide")

    # 条件路由
    graph.add_conditional_edges("decide", route_decision, {
        "act": "act",
        "reflect": "reflect",
    })

    graph.add_edge("act", END)
    graph.add_edge("reflect", END)

    compiled = graph.compile()
    logger.info("LangGraph agent compiled successfully")
    return compiled


# ─── 全局 Agent 单例 ───────────────────────────
_agent = None
_agent_lock = threading.Lock()


def get_agent():
    """获取全局 Agent 实例（线程安全）"""
    global _agent
    if _agent is None:
        with _agent_lock:
            if _agent is None:
                _agent = build_graph()
    return _agent
