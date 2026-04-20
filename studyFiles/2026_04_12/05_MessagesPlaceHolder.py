import os

from langchain_core.messages import HumanMessage
from langchain_core.output_parsers import StrOutputParser  # 原始结构化解析器
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI
from pydantic import SecretStr

model = ChatOpenAI(
    model="qwen3-max",
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
    api_key=SecretStr(os.getenv("DASHSCOPE_API_KEY")),
    streaming=True,
    temperature=0.7)

# ================================确定消息================================
prompt = ChatPromptTemplate.from_messages([
    ("system", "你是我的小助手，名叫{model_name}"),
    ("human", "我的问题是：{question}")]
)

parse = StrOutputParser()

chain = prompt | model | parse

for chunk in chain.stream({"model_name": "小智", "question": "你叫什么？1+1=？"}):
    print(chunk, end="", flush=True)

# ================================不确定消息================================

prompt = ChatPromptTemplate.from_messages([
    ("system", "你是我的小助手，名叫{model_name}"),
    # 如果我不知道这个问题是什么。我就可以使用MessagePlaceholder，如：
    MessagesPlaceholder(variable_name="msgs")]
)

parse = StrOutputParser()

chain = prompt | model | parse

for chunk in chain.stream({"model_name": "小智", "msgs": [HumanMessage(content="你叫什么？1+1=？")]}):
    print(chunk, end="", flush=True)
