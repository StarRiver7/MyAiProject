"""
Few-shot 与实例选择器学习笔记（LangChain）
=================================================

本文件总结 3 个核心组件：
1) FewShotPromptTemplate（文本提示词 few-shot）
2) FewShotChatMessagePromptTemplate（对话消息 few-shot）
3) Example Selector（实例选择器）
"""

# =========================
# 一、知识点总结
# =========================
#
# 1. FewShotPromptTemplate 是什么？
#    - 用于“纯文本 Prompt”场景，把多个示例拼接到最终提示词中。
#    - 典型结构：prefix + examples + suffix。
#    - 常见用途：格式约束、风格迁移、固定任务模式（分类、改写、抽取）。
#
# 2. FewShotChatMessagePromptTemplate 是什么？
#    - 用于“聊天消息 Prompt”场景（system/human/ai 多消息结构）。
#    - 示例本身也是“消息对”（human -> ai）。
#    - 常见用途：聊天机器人、多轮任务、对话式 agent 说明。
#
# 3. 为什么要实例选择器（Example Selector）？
#    - 手动固定 examples 有局限：输入变化大时，示例可能不相关。
#    - 实例选择器能根据当前用户输入，动态挑选最相关示例。
#    - 好处：更稳、更省 token（只放最相关的 K 条）。
#
# 4. 常见实例选择器类型：
#    - LengthBasedExampleSelector：按长度控制示例数量，避免超上下文。
#    - SemanticSimilarityExampleSelector：按语义相似度选最相关示例。
#    - MaxMarginalRelevanceExampleSelector（MMR）：兼顾相关性与多样性。
#
# 5. 实战建议：
#    - 示例数量通常 2~6 条起步，太多会增加 token 成本。
#    - 示例字段命名要统一（如 input/output）。
#    - 示例尽量覆盖边界情况（短文本、歧义、特殊格式）。
#    - 先用固定 few-shot 验证效果，再升级到动态选择器。


# =========================
# 二、案例 1：FewShotPromptTemplate（文本）
# =========================
def demo_few_shot_prompt_template():
    from langchain_core.prompts import PromptTemplate, FewShotPromptTemplate

    # 训练示例：英译中
    examples = [
        {"en": "I love programming.", "zh": "我热爱编程。"},
        {"en": "How are you?", "zh": "你好吗？"},
        {"en": "This is a book.", "zh": "这是一本书。"},
    ]

    # 单条示例格式
    example_prompt = PromptTemplate.from_template("英文: {en}\n中文: {zh}")

    # few-shot 总模板
    few_shot_prompt = FewShotPromptTemplate(
        examples=examples,
        example_prompt=example_prompt,
        prefix="你是一个翻译助手，请参考以下示例完成翻译：",
        suffix="英文: {query}\n中文:",
        input_variables=["query"],
        example_separator="\n\n",
    )

    final_prompt = few_shot_prompt.format(query="The weather is nice today.")
    print("\n=== 案例1：FewShotPromptTemplate ===")
    print(final_prompt)


# =========================
# 三、案例 2：FewShotChatMessagePromptTemplate（对话消息）
# =========================
def demo_few_shot_chat_message_prompt_template():
    from langchain_core.prompts import (
        ChatPromptTemplate,
        FewShotChatMessagePromptTemplate,
    )

    # 对话示例：用户提问 -> 助手回答
    examples = [
        {"input": "请把'苹果'翻译成英文", "output": "apple"},
        {"input": "请把'香蕉'翻译成英文", "output": "banana"},
    ]

    # 每条示例由两条消息组成（human + ai）
    example_prompt = ChatPromptTemplate.from_messages(
        [
            ("human", "{input}"),
            ("ai", "{output}"),
        ]
    )

    few_shot_messages = FewShotChatMessagePromptTemplate(
        examples=examples,
        example_prompt=example_prompt,
    )

    # 组装最终聊天模板
    final_prompt = ChatPromptTemplate.from_messages(
        [
            ("system", "你是一个中英词汇翻译助手，回答简洁准确。"),
            few_shot_messages,
            ("human", "{query}"),
        ]
    )

    messages = final_prompt.format_messages(query="请把'西瓜'翻译成英文")
    print("\n=== 案例2：FewShotChatMessagePromptTemplate ===")
    for m in messages:
        print(f"[{m.type}] {m.content}")


# =========================
# 四、案例 3：语义相似度实例选择器
# =========================
def demo_semantic_similarity_example_selector():
    """
    该案例演示：
    - 从若干分类示例中，基于当前输入动态选最相关示例
    - 再交给 FewShotPromptTemplate 拼接成最终提示词
    """
    from langchain_core.prompts import PromptTemplate, FewShotPromptTemplate
    from langchain_core.example_selectors import SemanticSimilarityExampleSelector
    from langchain_openai import OpenAIEmbeddings
    from langchain_community.vectorstores import FAISS

    examples = [
        {"text": "这家餐厅菜很好吃，服务也很棒", "label": "正向"},
        {"text": "快递太慢了，包装还破损", "label": "负向"},
        {"text": "电影剧情一般，但是画面不错", "label": "中性"},
        {"text": "客服态度恶劣，体验很差", "label": "负向"},
        {"text": "产品质量超出预期，下次还会买", "label": "正向"},
    ]

    example_prompt = PromptTemplate.from_template("文本: {text}\n情感: {label}")

    # 语义相似度选择器：每次挑最相近的 2 条示例
    selector = SemanticSimilarityExampleSelector.from_examples(
        examples=examples,
        embeddings=OpenAIEmbeddings(),  # 需要设置 OPENAI_API_KEY
        vectorstore_cls=FAISS,
        k=2,
        input_keys=["text"],
    )

    few_shot_prompt = FewShotPromptTemplate(
        example_selector=selector,
        example_prompt=example_prompt,
        prefix="请根据示例判断文本情感（正向/中性/负向）：",
        suffix="文本: {text}\n情感:",
        input_variables=["text"],
        example_separator="\n\n",
    )

    query = "售后响应及时，问题很快解决了"
    final_prompt = few_shot_prompt.format(text=query)
    print("\n=== 案例3：SemanticSimilarityExampleSelector ===")
    print(final_prompt)


if __name__ == "__main__":
    # 按需取消注释运行
    demo_few_shot_prompt_template()
    demo_few_shot_chat_message_prompt_template()

    # 该示例依赖 embeddings API key，未配置可先不运行
    # demo_semantic_similarity_example_selector()
