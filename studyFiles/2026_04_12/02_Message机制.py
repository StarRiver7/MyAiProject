# =============================================================================
# Message 机制（消息机制）—— 与大模型对话时的「结构化上下文」
# =============================================================================
#
# 一、为什么需要 Message？
#
#   聊天模型 API（OpenAI 兼容格式等）不把「一整段长字符串」当成唯一输入，而是接收
#   一条有序的消息列表 messages。每条消息至少包含：
#     • role（角色）：谁在说话 —— 常见为 system / user / assistant / tool
#     • content（内容）：说了什么
#
#   这样模型能区分：系统指令、用户问题、助手历史回复、工具返回结果，从而正确续写
#   多轮对话、做工具调用、遵守系统人设等。
#
# 二、常见 role 含义（与 LangChain 类对应）
#
#   • system  → SystemMessage     全局规则、人设、输出格式要求（可选但常用）
#   • user    → HumanMessage      终端用户或「人类侧」输入
#   • assistant → AIMessage       模型上一轮的回复；多轮对话时必须拼进 history
#   • tool    → ToolMessage       函数/插件执行结果，供模型在下一轮 reasoning 使用
#
# 三、两种写法：字典 vs LangChain 消息对象
#
#   API 层往往是 list[dict]；LangChain 用消息类封装同一信息，便于类型检查、与
#   ChatPromptTemplate / LCEL 链式组合。二者语义一致，可按场景互换或转换。
#
# 四、多轮对话要点
#
#   顺序一般为：system（可选）→ user → assistant → user → assistant → …
#   漏掉 assistant 或顺序乱了，模型会「失忆」或把上下文理解错。
#
# 五、更贴合公司落地的方式（学习时建议按这个优先级）
#
#   1) 先吃透「协议层」：OpenAI 兼容的 messages = [{role, content}, ...]
#      这是各厂商文档、网关、日志、联调时最常见的形状，面试也常问「多轮怎么拼」。
#
#   2) 业务代码里少写「散落的长字符串」：用 ChatPromptTemplate（或独立 .md/.yaml
#      提示词文件 + 加载）把 system / user 模板和变量分开，方便改文案、做版本对比、
#      和 15_项目总结.py 一样用 partial 注入固定块（如 format_instructions）。
#
#   3) 编排选型：很多团队用 LangChain / LlamaIndex 做 RAG、Agent、链式调用；也有团队
#      只用官方 SDK + 自研薄封装。两条路都要会「消息列表 + 多轮 + 工具返回」这一套语义，
#      框架只是语法糖。
#
#   4) 典型分层：Template / Message 对象（应用内）→ 请求前转成 dict（调用供应商 API）→
#      落库/可观测性（trace 里常存脱敏后的 messages）。你写学习项目时模仿这条线即可。
#
# =============================================================================

from __future__ import annotations

import os
from typing import Any

from langchain_core.messages import (
    AIMessage,
    BaseMessage,
    HumanMessage,
    SystemMessage,
    ToolMessage,
)
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from pydantic import SecretStr


# -----------------------------------------------------------------------------
# 案例 1：字典形式（贴近 HTTP API / 原生 SDK）
# -----------------------------------------------------------------------------

def demo_messages_as_dicts() -> list[dict[str, Any]]:
    """与 OpenAI 风格 chat.completions 的 messages 字段一致。"""
    return [
        {"role": "system", "content": "你是简洁的中文助手，回答不超过三句话。"},
        {"role": "user", "content": "用一句话解释什么是 Token。"},
    ]


# -----------------------------------------------------------------------------
# 案例 2：LangChain 消息对象（推荐在 LangChain 链里使用）
# -----------------------------------------------------------------------------

def demo_messages_as_lc_objects() -> list[BaseMessage]:
    """与案例 1 语义等价，用类型化的 Message 类表示。"""
    return [
        SystemMessage(content="你是简洁的中文助手，回答不超过三句话。"),
        HumanMessage(content="用一句话解释什么是 Token。"),
    ]


def demo_print_message_structure() -> None:
    """不调用模型：只观察消息对象的类型与 content。"""
    msgs = demo_messages_as_lc_objects()
    for i, m in enumerate(msgs):
        print(f"[{i}] {type(m).__name__} -> {m.content[:40]}...")


# -----------------------------------------------------------------------------
# 案例 3：多轮对话 —— 必须把历史 AIMessage 放进列表
# -----------------------------------------------------------------------------

def demo_multi_turn_messages() -> list[BaseMessage]:
    """
    第二轮用户说「同上」时，模型若看不到第一轮 assistant 的回复，就无法解析「同上」。
    因此 history 中要包含完整的 user / assistant 交替片段（system 通常只放一次在最前）。
    """
    return [
        SystemMessage(content="你是编程小助手，回答简短。"),
        HumanMessage(content="Python 里 list 和 tuple 区别？"),
        AIMessage(content="list 可变、tuple 不可变；tuple 常作字典键等。"),
        HumanMessage(content="同上，各举一个适用场景。"),
    ]


# -----------------------------------------------------------------------------
# 案例 4：ToolMessage —— 函数调用 / 插件流程中的一环
# -----------------------------------------------------------------------------
#
# 典型流程（概念）：
#   user 提问 → 模型返回 tool_calls → 你的代码执行工具 → 把结果封装为 ToolMessage
#   （带 tool_call_id 与 name）→ 再次 invoke，模型根据工具结果生成最终自然语言回答。
#
# 下面仅演示「如何构造」一条工具结果消息，不执行真实工具调用。

def demo_tool_message_shape() -> ToolMessage:
    return ToolMessage(
        content='{"celsius": 22, "city": "上海"}',
        tool_call_id="call_mock_001",
        name="get_weather",
    )


# -----------------------------------------------------------------------------
# 案例 5：ChatPromptTemplate 与 Message —— 模板负责「生成消息列表」
# -----------------------------------------------------------------------------

def build_prompt_template() -> ChatPromptTemplate:
    """元组形式 ("system", "...") / ("human", "...") 最终会格式化成消息列表。"""
    return ChatPromptTemplate.from_messages(
        [
            ("system", "你是{domain}领域的助教，用中文回答。"),
            ("human", "请解释概念：{concept}"),
        ]
    )


def demo_template_to_messages() -> list[BaseMessage]:
    tpl = build_prompt_template()
    return tpl.format_messages(domain="机器学习", concept="过拟合")


# -----------------------------------------------------------------------------
# 案例 6（可选）：真实调用 —— 需要环境变量 DASHSCOPE_API_KEY
# -----------------------------------------------------------------------------

def run_live_if_configured() -> None:
    key = os.getenv("DASHSCOPE_API_KEY")
    if not key:
        print("未设置 DASHSCOPE_API_KEY，跳过在线调用。以上案例已覆盖 Message 结构与用法。")
        return

    model = ChatOpenAI(
        model="qwen3-max",
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
        api_key=SecretStr(os.getenv("DASHSCOPE_API_KEY")),
        temperature=0.7,
    )
    print("--- 单轮 ---")
    r = model.invoke(demo_messages_as_lc_objects())
    print(r.content)
    print("\n--- 多轮（含历史 AIMessage）---")
    r2 = model.invoke(demo_multi_turn_messages())
    print(r2.content)


if __name__ == "__main__":
    print("========== 案例：消息对象结构 ==========")
    demo_print_message_structure()
    print("\n========== 案例：模板 format_messages ==========")
    for m in demo_template_to_messages():
        print(type(m).__name__, "->", m.content[:60])
    print("\n========== 案例：ToolMessage 字段 ==========")
    tm = demo_tool_message_shape()
    print(tm)
    print("\n========== 案例：API 风格字典 ==========")
    print(demo_messages_as_dicts())
    print("\n========== 可选：在线调用 ==========")
    run_live_if_configured()
