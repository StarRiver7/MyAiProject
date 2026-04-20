# 任务： 结构化简历信息提取器

# 步骤：
# 简历文本输入
# ↓
# ChatPromptTemplate（注入格式指令）
# ↓
# ChatOpenAI（大模型提取信息）
# ↓
# OutputFixingParser（修复格式 + 解析）
# ↓
# PydanticOutputParser（校验数据结构）
# ↓
# Resume 对象（model_dump 转字典/JSON）
# ↓
# 异常时 → 兜底默认值

import os
from typing import Dict

from langchain_classic.output_parsers import OutputFixingParser  # 导入输出修复解析器
from langchain_core.output_parsers import PydanticOutputParser  # 原始结构化解析器
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, SecretStr, Field

model = ChatOpenAI(
    model="qwen3-max",
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
    api_key=SecretStr(os.getenv("DASHSCOPE_API_KEY")),
    streaming=True,
    temperature=0.7)


class Education(BaseModel):
    school: str = Field(..., title="学校")
    degree: str = Field(..., pattern="^(本科|大专|硕士|博士)$", title="学历")
    major: str = Field(..., title="专业")


class Resume(BaseModel):
    name: str = Field(..., min_length=1, title="姓名")
    age: int = Field(..., ge=18, title="年龄")
    gender: str = Field(..., pattern="^(男|女)$")
    email: str = Field(..., pattern="^[a-zA-Z0-9_-]+@[a-zA-Z0-9_-]+(\.[a-zA-Z0-9_-]+)+$")
    phone: str = Field(..., pattern="^1[3-9][0-9]{8}$")
    education: list[Education] = Field(default=[], title="教育经历")
    hobby: str = Field(...)


# 原始解析器
parser = PydanticOutputParser(pydantic_object=Resume)

# 带修复能力的解析器（容错机制）
fixing_parser = OutputFixingParser.from_llm(
    parser=parser,
    llm=model,
    max_retries=3
)

# 获取格式指令
format_instructions = fixing_parser.parser.get_format_instructions()

# 聊天提示词模板（多角色）
prompt = ChatPromptTemplate.from_messages([
    ("system", "你是一个文本助手，必须遵守格式{format_instructions}"),
    ("human", "请提取以下简历的信息：\n{resume_text}")
])

# 预先注入格式指令
prompt = prompt.partial(format_instructions=parser.get_format_instructions())

chain = prompt | model | fixing_parser

# 示例简历文本
# resume_text = """
# 张三，男，28岁
# 邮箱：zhangsan@qq.com
# 电话：13800138000
#
# 教育背景：
# - 北京大学 计算机科学与技术 本科
# - 清华大学 软件工程 硕士
#
# 工作经历：
# - 2020-2023 阿里巴巴 后端工程师
# - 2023至今 字节跳动 高级开发工程师
#
# 技能：Python, Java, MySQL, Redis, Docker
# """

# 这里不存在@，输出的格式却有@。是因为大模型基于常识和 pattern 约束自动修正
resume_text = "我叫李四，21岁。来自成都，邮箱：zhangsanqq.com，电话：13800138000，目前在成都东软学院就读本科。喜欢Java、音乐和篮球。"

try:
    # 执行提取（同步调用，等待完整结果）
    result = chain.invoke({"resume_text": resume_text})

    # 转为字典（便于存储）
    print("=== 字典格式 ===")
    print(result.model_dump())

    # 转为 JSON（便于接口返回）
    print("\n=== JSON格式 ===")
    print(result.model_dump_json(indent=2, ensure_ascii=False))

except Exception as e:
    # 兜底方案
    print(f"提取失败：{e}")
    fallback = Resume(name="未知", age=0, email="", phone="")


# ==========================================================
# 不使用管道符:

# 1. 填充提示词变量
filled_prompt = prompt.invoke({"resume_text": resume_text})

# 2. 调用大模型
model_response = model.invoke(filled_prompt)

# 3. 手动解析结果（带修复能力）
result = fixing_parser.parse(model_response.content)

# 4. 输出结果
print("=== 字典格式 ===")
print(result.model_dump())

print("\n=== JSON格式 ===")
print(result.model_dump_json(indent=2, ensure_ascii=False))

# ==========================================================
