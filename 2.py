from openai import OpenAI
from openai.types.chat.chat_completion import ChatCompletion
import os

# 1.获取client对象
client:OpenAI = OpenAI(
    api_key=os.getenv("DASHSCOPE_API_KEY"),
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
)

response:ChatCompletion = client.chat.completions.create(
    model="qwen3-max",
    messages=[
        {"role" : "system", "content" : "你是四川华西医院的就医小助手，专门为顾客提供就诊帮助,在必要的时候需要提醒患者谨遵医嘱！"},
        {"role" : "user", "content" : "你是谁？能做什么？简要回答我"}
    ],
    stream = True
)

for chunk in response:
    if chunk.choices[0].delta.content:
        print(chunk.choices[0].delta.content,
              end="",
              flush=True)