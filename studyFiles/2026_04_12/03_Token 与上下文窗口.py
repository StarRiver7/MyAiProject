# =============================================================================
# Token 与上下文窗口 —— 计费单位、长度上限与工程上的裁剪策略
# =============================================================================
#
# 一、Token 是什么？（和本文件案例的关系）
#
#   模型按自己的分词器把文本切成 Token；计费、限速、窗口上限都以 Token 计。
#   下面「窗口有多大」本质上是「这一请求里一共允许多少个 Token」。
#
# -----------------------------------------------------------------------------
# 二、上下文窗口（Context window）—— 概念
# -----------------------------------------------------------------------------
#
#   定义：单次调用中，模型在「这一轮推理」里能够读入的全部文本（以 Token 计量）的上限。
#   通常包括：system 提示、多轮对话历史、本轮用户问题、工具/插件返回、RAG 检索到的片段等。
#
#   类比：窗口像一张固定大小的书桌台面——东西堆得超过台面，要么放不下（API 报错），要么
#   必须把旧东西先拿走（截断、摘要、不塞进模型），否则新文件没地方摆。
#
#   和「模型有没有记忆」的区别：大模型默认不会在多轮之间自动永久记住你；所谓「记得」，
#   其实是「上一轮的原文又出现在本次的 messages 里」。窗口越小或截得越狠，丢掉的原文越多，
#   看起来就像「失忆」。
#
#   硬限制 vs 软体验：未到 API 上限也可能变「难用」——上下文极长时，模型对中间细节的关注
#   可能变弱（研究和工程上常称类似现象为「信息淹没 / lost in the middle」等），回答更容易
#   含糊或编造，这就是很多人说的「像幻觉」。
#
# -----------------------------------------------------------------------------
# 三、窗口太大或塞太满时，「失忆」「幻觉」从哪来？有什么办法？
# -----------------------------------------------------------------------------
#
#   常见原因（口语化对应你的感受）：
#
#   • 「失忆」：旧对话被截掉、没进本次 messages，或摘要丢掉了关键条件；模型根本「没看见」，
#     不是故意忘。
#   • 「幻觉」：缺口处模型会靠统计规律「补全」听起来合理的句子；上下文噪声多、指令不清、
#     又没有要求引用依据时，更容易瞎编。
#
#   可行对策（从易到难，常组合使用）：
#
#   1) 控制进窗内容：滑动窗口只保留最近 N 轮；system 与关键约束尽量短而稳定。
#   2) 历史摘要：对更早对话做周期性压缩（注意摘要要可审计，重要事实可结构化存库）。
#   3) RAG：长知识放向量库/搜索引擎，检索 Top-K 片段再拼进 prompt，而不是全文硬塞。
#   4) 外部记忆：会话级键值、用户画像、业务单据 ID 等存数据库，需要时用工具查询再注入。
#   5) 产品策略：主动澄清、分步任务、让用户确认关键信息，减少模型「猜」的空间。
#   6) 输出约束：要求「不知就说不知」、引用片段编号、JSON 模式等，降低胡编概率（不能 100%）。
#
#   本文件中的 trim_messages、粗算 token、预留 max_output，都属于「控制进窗 + 别顶满」这一层。
#
# -----------------------------------------------------------------------------
# 四、企业里通常怎么做？（对照上面的概念与对策）
# -----------------------------------------------------------------------------
#
#   • 网关 / BFF：统一校验 prompt 长度、限流、计费；超阈值直接拦截或触发裁剪，避免打到模型才炸。
#   • 会话存储：Redis/DB 存全量对话；应用层决定「每次调用带哪一段进窗口」，而不是指望模型记住。
#   • 裁剪策略：生产上常见「保留 system + 最近 K 轮」或「摘要 + 最近轮」；关键业务会配可观测指标
#     看截断率、用户投诉率。
#   • RAG 管线：文档切块、embedding、向量库（如 Milvus/PGVector）、重排序；只把相关 chunk 塞进
#     上下文，并常要求回答带引用，便于稽核。
#   • 观测与对账：日志里打 token_usage、模型名、是否截断；成本看板按项目/租户拆分。
#   • 合规与安全：PII 脱敏后再进窗；审计要能还原「当时模型到底看到了什么」。
#
# =============================================================================

from __future__ import annotations

import os
import re
from typing import Iterable

from langchain_core.messages import (
    AIMessage,
    BaseMessage,
    HumanMessage,
    SystemMessage,
    trim_messages,
)
from langchain_openai import ChatOpenAI
from pydantic import SecretStr


# -----------------------------------------------------------------------------
# 案例 1：粗算 Token（无第三方依赖，适合「是否可能超长」的快速预检）
# -----------------------------------------------------------------------------

# 【干什么】把任意字符串转成一个「大概有多少 token」的整数，用来做排序、告警、是否要先裁剪。
# 【为什么这样做】真实计费用的是厂商分词器，本地往往拿不到；但业务上需要在「发请求前」
#   就知道会不会太长，所以不能干等 API 报错。用经验公式零依赖、速度快，够用做门禁。
# 【注意】结果不精确，不能拿这个数和账单对账。
def rough_token_estimate(text: str) -> int:
    """见上方「干什么 / 为什么」。实现上：英文按约 4 字符≈1 token，非英文块按约 1.2 倍字数估算。"""
    if not text.strip():
        return 0
    ascii_letters = re.findall(r"[A-Za-z]+", text)
    ascii_part = sum(len(w) for w in ascii_letters)
    non_ascii = len(re.sub(r"[A-Za-z\s]", "", text))
    return max(1, int(ascii_part / 4 + non_ascii * 1.2))


# 【干什么】打印多句示例，让你对比「不同语言混合」时 rough_token_estimate 的大致量级。
# 【为什么这样做】数字单独看抽象；和例句一起看，你才能建立「多长算危险」的直觉。
def demo_rough_estimate() -> None:
    samples = [
        "Hello world from LangChain",
        "用一句话解释上下文窗口。",
        "Mixed 混合 English 与 中文 的 句子。",
    ]
    for s in samples:
        print(f"rough≈{rough_token_estimate(s):4d}  |  {s[:40]}...")


# -----------------------------------------------------------------------------
# 案例 2：tiktoken（OpenAI GPT 系常用编码；其它模型仅作参考）
# -----------------------------------------------------------------------------

# 【干什么】用 OpenAI 公开的 cl100k_base 编码器，数出这段文本在该编码下有多少个 token。
# 【为什么这样做】在和 GPT 系列对接时，tiktoken 的数和官方用量往往很接近，适合本地预检、
#   单测、离线算 prompt 长度。国产模型分词表不同，这里只能当「参考」，最终仍以 API 返回为准。
# 【为什么 try/except】环境里未必装了 tiktoken，装了再算，没装就返回 None，主程序好分支处理。
def count_tokens_tiktoken_cl100k(text: str) -> int | None:
    """见上方。未安装 tiktoken 时返回 None。"""
    try:
        import tiktoken
    except ImportError:
        return None
    enc = tiktoken.get_encoding("cl100k_base")
    return len(enc.encode(text))


# 【干什么】演示调用 count_tokens_tiktoken_cl100k，在控制台打出一句英文的 token 数。
# 【为什么这样做】把「库函数」和可观察输出绑在一起，你跑 __main__ 立刻能验证 tiktoken 是否可用。
def demo_tiktoken_if_available() -> None:
    text = "Tokenization splits text into subword units."
    n = count_tokens_tiktoken_cl100k(text)
    if n is None:
        print("未安装 tiktoken，跳过。可执行: pip install tiktoken")
    else:
        print(f"tiktoken(cl100k_base)={n}  |  {text}")


# -----------------------------------------------------------------------------
# 案例 3：为「回复」预留输出预算（概念）
# -----------------------------------------------------------------------------

# 【干什么】根据「模型总上下文上限」和「你希望回复最多多长」，算出一个「输入最好别超过多少」的提示值。
# 【为什么这样做】很多人只算 prompt 没超窗口，却忘了模型还要生成 completion；两者共用同一条
#   上下文预算，挤爆了就会导致回答被截断或请求失败。先留出口子，是线上排错最常见的经验。
# 【为什么减 64】真实协议里还有少量模板开销，这里用固定常数示意「要留余量」，具体以厂商文档为准。
def describe_context_budget(context_limit: int, max_output: int) -> dict[str, int]:
    """见上方。返回字典方便打印、接日志或单测断言。"""
    safe_input_budget = max(0, context_limit - max_output - 64)
    return {
        "context_limit": context_limit,
        "max_output_reserved": max_output,
        "safe_input_budget_hint": safe_input_budget,
    }


# -----------------------------------------------------------------------------
# 案例 4：LangChain 自带 trim_messages —— 按 token 预算保留「最近」对话
# -----------------------------------------------------------------------------

# 【干什么】造一段「很长」的多轮消息列表（system + 多轮问答），专门用来演示裁剪。
# 【为什么这样做】trim_messages 需要输入数据；用程序拼接长字符串，比手工粘贴稳定、可重复运行。
def build_long_fake_history() -> list[BaseMessage]:
    return [
        SystemMessage(content="你是客服助手，回答简短。"),
        HumanMessage(content="问题1：" + "用户反馈" * 80),
        AIMessage(content="答复1：" + "我们会记录" * 80),
        HumanMessage(content="问题2：" + "物流很慢" * 80),
        AIMessage(content="答复2：" + "已催促仓库" * 80),
        HumanMessage(content="最新：仅退款怎么操作？"),
    ]


# 【干什么】调用 LangChain 的 trim_messages：在不超过 max_tokens（近似）的前提下，尽量保留「末尾」的消息。
# 【为什么这样做】企业里多轮对话最容易爆窗口；「丢最旧、留最新」是最常见策略之一，且要和
#   system 提示词一起保留（include_system=True），否则人设会丢。这里用 token_counter="approximate"
#   是为了示例不依赖具体模型密钥也能跑；上线可对齐你们用的模型的计数方式。
def demo_trim_messages() -> None:
    raw = build_long_fake_history()
    trimmed = trim_messages(
        raw,
        max_tokens=120,
        strategy="last",
        token_counter="approximate",
        include_system=True,
    )
    print(f"裁剪前 {len(raw)} 条 → 裁剪后 {len(trimmed)} 条")
    for m in trimmed:
        preview = (m.content[:50] + "…") if len(m.content) > 50 else m.content
        print(f"  {type(m).__name__}: {preview}")


# -----------------------------------------------------------------------------
# 案例 5：列表消息的总粗算（发请求前的简单门禁）
# -----------------------------------------------------------------------------

# 【干什么】把一整条对话（多条 BaseMessage）的 content 粗算 token 并求和，得到「整次请求输入大概多长」。
# 【为什么这样做】网关、限流、熔断通常看「整包」长度；单条消息不够。这里复用 rough_token_estimate，
#   保持和案例 1 同一套估算标准，避免每处各写一套魔法数字。
# 【注意】本课所有消息的 content 都是 str；若你做多模态（图片等），content 可能是列表，要另写解析。
def total_rough_tokens(messages: Iterable[BaseMessage]) -> int:
    return sum(rough_token_estimate(m.content) for m in messages)


# 【干什么】用假数据算总粗算 token，和一个阈值比较，打印「通过」或「建议裁剪」。
# 【为什么这样做】演示「发请求前的门禁」长什么样：超了就不调用模型，先 trim/摘要，省钱也省报错。
def demo_gate_before_request() -> None:
    msgs = build_long_fake_history()
    total = total_rough_tokens(msgs)
    limit = 500
    print(f"粗算总输入 token≈{total}，阈值 {limit} → {'通过' if total <= limit else '建议裁剪或摘要'}")


# -----------------------------------------------------------------------------
# 案例 6（可选）：真实调用 —— 以响应里的 usage 为准（对齐公司监控方式）
# -----------------------------------------------------------------------------

# 【干什么】若配置了 DASHSCOPE_API_KEY，则真实调一次通义兼容接口，并打印模型回复 + 返回体里的用量字段。
# 【为什么这样做】前面都是「估算」，账单和监控以供应商返回为准；让你亲眼看到 usage_metadata /
#   token_usage，和以后接入日志、计费、看板是同一套数据。没配密钥就跳过，保证脚本在离线环境也能跑完。
def run_live_usage_if_configured() -> None:
    key = os.getenv("DASHSCOPE_API_KEY")
    if not key:
        print("未设置 DASHSCOPE_API_KEY，跳过在线演示。")
        return

    model = ChatOpenAI(
        model="qwen3-max",
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
        api_key=SecretStr(key),
        temperature=0.2,
    )
    reply = model.invoke([HumanMessage(content="用不超过20字介绍什么是 Token。")])
    print("模型回复:", reply.content)
    # LangChain 统一字段（若提供方返回用量）
    if reply.usage_metadata:
        print("usage_metadata:", reply.usage_metadata)
    if reply.response_metadata.get("token_usage"):
        print("response_metadata[token_usage]:", reply.response_metadata["token_usage"])


# 【干什么】脚本直接运行时，按从易到难打印各案例结果。
# 【为什么这样做】学习文件「打开就跑」最有感觉；离线案例在前，在线 usage 在最后且可跳过，避免没密钥就中断。
if __name__ == "__main__":
    print("========== 案例：粗算 token ==========")
    demo_rough_estimate()
    print("\n========== 案例：tiktoken（可选）==========")
    demo_tiktoken_if_available()
    print("\n========== 案例：上下文与输出预留 ==========")
    print(describe_context_budget(context_limit=128_000, max_output=4_096))
    print("\n========== 案例：trim_messages ==========")
    demo_trim_messages()
    print("\n========== 案例：请求前门控 ==========")
    demo_gate_before_request()
    print("\n========== 可选：在线 usage ==========")
    run_live_usage_if_configured()
