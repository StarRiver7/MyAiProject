# ====================== 第二部分：实战演示 - 逗号分隔列表解析器 + LCEL 链式流式输出 ======================
# 从 langchain_core.prompts 模块导入 PromptTemplate 类，用于构建基础提示词模板
import os

from langchain_core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from pydantic import SecretStr
from langchain_core.output_parsers import CommaSeparatedListOutputParser

# 1. 实例化 ChatOpenAI 大模型对象，配置相关参数
model = ChatOpenAI(
    model="qwen3-max",  # 指定使用的大模型名称（通义千问 qwen-plus）
    base_url= "https://dashscope.aliyuncs.com/compatible-mode/v1",  # 大模型服务接口地址（阿里云通义千问兼容 OpenAI 格式）
    api_key=SecretStr(os.getenv("DASHSCOPE_API_KEY")),  # 安全封装 API 密钥，防止明文暴露
    streaming=True,  # 关键参数：设置为 True 开启流式输出功能，模型分段返回生成结果
    temperature=0.7)  # 生成温度（0-2），0.7 兼顾生成内容的创造性和稳定性

# 2. 实例化逗号分隔列表解析器（用于将模型返回的逗号分隔字符串转为 Python 列表）
out_parser = CommaSeparatedListOutputParser()

# 3. 获取解析器的格式指令
# 自动生成格式要求，告诉大模型需要以“逗号分隔”的形式返回结果，确保解析器能正常解析
format_instructions = out_parser.get_format_instructions()

# 4. 创建基础提示词模板
prompt = PromptTemplate(
    template="""
    列举多个常见的{topic}场景。{format_instructions}
    """,  # 模板字符串：{topic} 接收主题变量，{format_instructions} 接收解析器格式指令
    input_variables=["topic"],  # 声明需要动态传入的变量（仅 topic，format_instructions 为固定参数）
    partial_variables={"format_instructions": format_instructions}  # 预先填充固定变量 format_instructions
)

# 5. 使用 LCEL 管道符（|）串联组件，构建完整链式流程
# 执行流程：prompt（填充 topic 生成完整提示词）→ model（流式调用大模型返回片段）→ out_parser（解析片段为列表元素）
chain = prompt | model | out_parser

# 6. 调用链的 stream 方法，实现流式输出
# 传入动态变量 topic = "电影"，遍历流式返回的解析结果（每个 token 是列表中的单个元素）
for token in chain.stream({"topic": "电影"}):
    # 实时打印每个解析后的列表元素
    print(token)


