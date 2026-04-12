# ====================== 核心功能：使用 StrOutputParser 字符串解析器，将大模型返回结果统一转为纯字符串格式 ======================
import os
from langchain_core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from pydantic import SecretStr
# 从 langchain_core.output_parsers 模块导入多种解析器
# StrOutputParser：字符串解析器（核心使用），CommaSeparatedListOutputParser：逗号分隔列表解析器，JsonOutputParser：JSON格式解析器
from langchain_core.output_parsers import StrOutputParser, CommaSeparatedListOutputParser, JsonOutputParser

# 1. 使用 PromptTemplate 类方法 from_template 快速创建提示词模板
# 模板字符串中 {topic} 为动态变量，用于接收需要写诗的主题内容
prompt = PromptTemplate.from_template("写一首关于{topic}的四句诗")

model = ChatOpenAI(
    model="qwen3-max",
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
    api_key=SecretStr(os.getenv("DASHSCOPE_API_KEY")),
    streaming=True,
    temperature=0.7)

# 3. 实例化 StrOutputParser 字符串解析器
# 核心本质：屏蔽不同大模型返回对象的底层格式差异，自动提取核心文本内容并转换为纯 Python 字符串
# 无需手动调用 response.content，解析器内部已自动完成核心文本提取
parse = StrOutputParser()

# 4. 使用 LCEL 管道符（|）串联组件，构建完整链式流程
# 执行流程：prompt（填充 topic 变量生成完整提示词）→ model（接收提示词调用大模型返回响应对象）→ parse（解析响应对象为纯字符串）
chain = prompt | model | parse

for chunk in chain.stream({"topic": "如何学习java"}):
    print(chunk, end="", flush=True)
