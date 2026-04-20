# =============================================================================
# Function Calling（工具调用）—— 原理与企业落地要点
# =============================================================================
#
# 一、它解决什么问题？
#
#   大模型只会「生成文本」，不能直接查库、下单、调内部 HTTP。工具调用让模型在需要时
#   「声明」要执行哪个函数、参数是什么；由你的服务真正执行（可控、可审计），再把结果
#   以 tool 消息塞回上下文，模型再组织自然语言回答用户。
#
# 二、协议层长什么样？（OpenAI 兼容思路，各厂商名称略不同）
#
#   1) 请求里除了 messages，还带 tools / functions：JSON Schema 描述每个工具的名称、说明、参数。
#   2) 模型两种输出之一：
#      • 普通回复：assistant 只有 content，无 tool_calls。
#      • 要调工具：assistant 带 tool_calls（含 id、name、arguments 等）。
#   3) 应用侧解析 tool_calls → 校验参数 → 执行真实逻辑（可能超时/失败）。
#   4) 为每个调用追加一条 role=tool 的消息（内容通常是字符串化结果），tool_call_id 必须与
#      上一步 id 对齐；再发第二轮请求，让模型根据工具结果生成最终答案。
#
#   核心：模型「提议」调用；执行权始终在服务端。这是和「让模型写代码自己跑」的本质区别。
#
# 三、企业里为什么必须多一层工程？（严格贴合落地）
#
#   • 白名单与权限：只注册业务允许的工具；按租户/角色决定可见工具；敏感操作二次确认或人工审批。
#   • 参数校验：不信任模型 JSON；用 Pydantic/JSON Schema 校验后再执行，防止注入、类型错误。
#   • 隔离与限流：工具内部调下游服务要超时、重试、熔断；禁止执行任意 shell/动态代码。
#   • 可观测性：结构化日志记录 tool 名称、call_id、耗时、成功/失败、脱敏后的参数与返回值。
#   • 幂等与审计：支付类接口要带幂等键；全链路 trace_id，满足合规留痕。
#   • 失败策略：工具报错时把错误信息封装进 ToolMessage，让模型对用户说「暂时查不到」，
#     而不是编造数据（需在 system 里约定）。
#
# =============================================================================

from __future__ import annotations

import json
import os
from typing import Any

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, ToolMessage
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from pydantic import SecretStr


# -----------------------------------------------------------------------------
# 案例 1：用 @tool 声明工具（企业里对应「对外暴露能力清单」）
# -----------------------------------------------------------------------------

# 【干什么】把「查天气」封装成带名称、描述、参数模式的工具对象，供 bind_tools 交给模型选型。
# 【为什么这样做】协议需要 JSON Schema；@tool 从类型注解和 docstring 自动生成，减少手写 Schema
#   出错。描述要写清「何时该用」，模型靠描述做路由。
@tool
def get_weather(city: str) -> str:
    """查询指定城市当前气温（摄氏度）。用户问到天气、气温、冷不冷时用此工具。"""
    # 企业里这里应是 HTTP/RPC/缓存；教学用固定映射，避免真打外网。
    table = {"北京": "5", "上海": "12", "深圳": "18"}
    c = city.strip()
    if c not in table:
        return json.dumps({"error": "unsupported_city", "city": c}, ensure_ascii=False)
    return json.dumps({"city": c, "celsius": table[c]}, ensure_ascii=False)


# 【干什么】第二个工具，演示「多工具路由」与不同返回形态。
# 【为什么这样做】生产环境常有多个 API；模型通过 description 区分何时查订单、何时查库存等。
@tool
def get_order_status(order_id: str) -> str:
    """根据订单号查询状态。用户明确提供订单号或要查物流/订单进度时用此工具。"""
    oid = order_id.strip().upper()
    if not oid.startswith("ORD-"):
        return json.dumps({"error": "invalid_order_id", "hint": "格式应为 ORD-数字"}, ensure_ascii=False)
    return json.dumps({"order_id": oid, "status": "已发货", "carrier": "顺丰"}, ensure_ascii=False)


TOOLS = [get_weather, get_order_status]


# -----------------------------------------------------------------------------
# 案例 2：仅观察工具元数据（不调模型，适合先理解「发给厂商的是什么」）
# -----------------------------------------------------------------------------

# 【干什么】打印工具名、说明、参数 Schema，对应请求体里 tools 字段的雏形。
# 【为什么这样做】联调时 80% 问题来自 Schema/描述不清；先离线核对再接模型，省时间。
def demo_print_tool_definitions() -> None:
    for t in TOOLS:
        print("---")
        print("name:", t.name)
        print("description:", t.description)
        print("args_schema:", t.args_schema.model_json_schema() if t.args_schema else None)


# -----------------------------------------------------------------------------
# 案例 3：手动编排「模型 → 执行工具 → 再模型」（企业 Agent/BFF 的核心循环）
# -----------------------------------------------------------------------------

# 【干什么】实现一轮或多轮 tool_calls 的执行，并把 ToolMessage 拼回 messages，直到模型不再要工具。
# 【为什么这样做】LangGraph / AgentExecutor 本质是包装此循环；手写一遍才能看懂日志、排错、加
#   权限校验与超时。企业常在循环里插入：鉴权、审计、限流、人工审批节点。
def run_tool_loop(
    model_with_tools: Any,
    user_text: str,
    max_tool_rounds: int = 3,
) -> list[BaseMessage]:
    messages: list[BaseMessage] = [HumanMessage(content=user_text)]
    tools_by_name = {t.name: t for t in TOOLS}

    for _ in range(max_tool_rounds):
        ai: AIMessage = model_with_tools.invoke(messages)
        messages.append(ai)

        if not ai.tool_calls:
            break

        for call in ai.tool_calls:
            # call: name, args, id（LangChain 已解析 args 为 dict）
            name = call["name"]
            args = call["args"]
            call_id = call["id"]
            tool_fn = tools_by_name.get(name)
            if tool_fn is None:
                payload = {"error": "unknown_tool", "name": name}
                messages.append(
                    ToolMessage(
                        content=json.dumps(payload, ensure_ascii=False),
                        tool_call_id=call_id,
                        name=name,
                    )
                )
                continue
            # 企业里：在此校验 args、鉴权、打点开始时间、try/except 包一层
            try:
                result = tool_fn.invoke(args)
            except Exception as e:  # noqa: BLE001 — 教学示例展示把异常喂回模型
                result = json.dumps({"error": "tool_execution_failed", "detail": str(e)}, ensure_ascii=False)
            messages.append(ToolMessage(content=str(result), tool_call_id=call_id, name=name))

    return messages


def print_conversation_tail(msgs: list[BaseMessage], last_n: int = 6) -> None:
    for m in msgs[-last_n:]:
        if isinstance(m, HumanMessage):
            print("Human:", m.content)
        elif isinstance(m, AIMessage):
            print("AI:", m.content or "(空 content，可能仅有 tool_calls)")
            if m.tool_calls:
                print("  tool_calls:", m.tool_calls)
        elif isinstance(m, ToolMessage):
            print("Tool:", m.name, "->", m.content[:200])


# -----------------------------------------------------------------------------
# 案例 4（可选）：接通义兼容接口跑通完整链路
# -----------------------------------------------------------------------------

# 【干什么】有 API Key 时绑定工具并跑 run_tool_loop，验证端到端。
# 【为什么这样做】与 02/03 文件一致的学习环境；无 Key 时跳过，不影响阅读注释与离线 demo。
def run_live_if_configured() -> None:
    key = os.getenv("DASHSCOPE_API_KEY")
    if not key:
        print("未设置 DASHSCOPE_API_KEY，跳过在线演示。")
        return

    base = ChatOpenAI(
        model="qwen3-max",
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
        api_key=SecretStr(key),
        temperature=0.2,
    )
    model_with_tools = base.bind_tools(TOOLS)

    print("========== 查询 A：天气 ==========")
    msgs = run_tool_loop(model_with_tools, "上海今天大概多少度？只要数字和城市。")
    print_conversation_tail(msgs)

    print("\n========== 查询 B：订单 ==========")
    msgs_b = run_tool_loop(model_with_tools, "帮我看看订单 ORD-10086 状态。")
    print_conversation_tail(msgs_b)


if __name__ == "__main__":
    print("========== 工具定义（离线）==========")
    demo_print_tool_definitions()
    print("\n========== 可选：在线 tool 循环 ==========")
    run_live_if_configured()
