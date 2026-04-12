# ====================== 核心功能：使用 JsonOutputParser 解析器，将大模型返回结果转为标准 JSON 格式并可直接按键取值 ======================
import os
from langchain_core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from pydantic import SecretStr
# StrOutputParser：字符串解析器（核心使用），CommaSeparatedListOutputParser：逗号分隔列表解析器，JsonOutputParser：JSON格式解析器
from langchain_core.output_parsers import StrOutputParser, CommaSeparatedListOutputParser, JsonOutputParser

model = ChatOpenAI(
    model="qwen3-max",
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
    api_key=SecretStr(os.getenv("DASHSCOPE_API_KEY")),
    streaming=True,
    temperature=0.7)

# 2. 实例化 JsonOutputParser JSON 解析器
# 核心本质：1. 自动识别大模型返回的 JSON 格式字符串，将其转换为 Python 可直接操作的字典（dict）对象
#          2. 若大模型返回非标准 JSON，会尝试容错解析；若完全不符合 JSON 格式，会抛出解析异常
parse = JsonOutputParser()

# 3. 构建提示词模板（核心：明确要求大模型返回指定结构的 JSON 格式，确保 JsonOutputParser 能正常解析）
# 模板中通过清晰的 JSON 示例结构，约束大模型返回包含 "answer"（答案文本）和 "confidence"（0-1区间置信度）的 JSON
# 问题:{question} 为动态变量，用于接收用户的具体问题
# 说明：模板中使用 {{ }} 是转义写法，最终会渲染为单个 { }，用于指定JSON格式中的大括号
prompt = PromptTemplate.from_template("""
    回答以下问题，返回json格式:
    {{
        "answer":"答案文本",
        "confidence": 置信度(0-1)
    }}
    问题:{question}
""")

# 4. 使用 LCEL 管道符（|）串联组件，构建完整链式流程
# 执行流程：prompt（填充 question 变量生成含 JSON 格式要求的完整提示词）→ model（调用大模型返回 JSON 格式字符串响应）→ parse（将 JSON 字符串解析为 Python 字典）
chain = prompt | model | parse

# 5. 调用链的 invoke 方法，传入具体问题执行流程，获取解析后的 Python 字典结果
# 传入字典格式参数，key 对应模板中的 {question} 变量，value 为具体问题（此处为“地球的半径是多少?”）
result = chain.invoke({"question": "地球的半径是多少?"})

# 6. 打印解析后的完整字典结果（可直观看到 JSON 解析后的键值对结构）
print(result)

# 7. 按键取值，分别获取答案文本和置信度，实现精准数据提取与使用
# 由于 result 是 Python 字典对象，可直接通过 ["key"] 的方式获取对应值，方便后续业务逻辑处理
print(f"答案:{result['answer']},置信度:{result['confidence']}")
