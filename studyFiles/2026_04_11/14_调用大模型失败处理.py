# ====================== 大模型输出修复机制：OutputFixingParser 核心使用（项目级应用） ======================
# OutputFixingParser 核心价值：大模型返回结果可能不符合格式要求，该工具可自动修复格式错误并重新解析
# 支持设置重试次数，基于原始解析器约束，让大模型修正输出后再进行解析，提升结构化提取的成功率
# 若多次重试仍失败，常见原因：1.模型能力不足 2.网络异常导致输出不完整 3.提示词描述不具体、约束不明确
import os

from langchain_classic.output_parsers import OutputFixingParser  # 导入输出修复解析器
from langchain_core.output_parsers import PydanticOutputParser  # 原始结构化解析器
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, SecretStr

model = ChatOpenAI(
    model="qwen3-max",
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
    api_key=SecretStr(os.getenv("DASHSCOPE_API_KEY")),
    streaming=True,
    temperature=0.7)


# 第1步：定义数据结构（约束输出格式）
class Actor(BaseModel):
    name: str
    film_names: list[str]

# 第2步：创建原始解析器（只会解析，不会修复）
parser = PydanticOutputParser(pydantic_object=Actor)

# 第3步：包装成带修复能力的解析器
fixing_parser = OutputFixingParser.from_llm(
    parser=parser,      # 原始解析器
    llm=model,          # 用于修复的大模型
    max_retries=3       # 最多重试3次
)

# 第4步：解析错误格式（自动修复）
misformatted_output = """ {'name':'','film_names':['A计划','B计划']} """
fixed_data = fixing_parser.parse(misformatted_output)
# 内部流程：
# 1. parser.parse() 失败（单引号不符合JSON规范）
# 2. 告诉 model："这个输出有错，应该用双引号"
# 3. model 返回：'{"name": "", "film_names": ["A计划", "B计划"]}'
# 4. parser.parse() 成功 → 返回 Actor 对象

