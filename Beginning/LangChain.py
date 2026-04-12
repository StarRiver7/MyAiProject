# from openai import OpenAI
from dashscope import api_key
from langchain_community.chat_models.tongyi import ChatTongyi
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
import os

from openai import Stream
from pyexpat.errors import messages

# def get_response():
#     client = OpenAI(
#         api_key=os.getenv("DASHSCOPE_API_KEY"),
#         base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
#     )
#
#     completion = client.chat.completions.create(
#         model="qwen-plus",
#         # SystemMessage(content="你是四川华西医院的助诊助手，请为用户解答问题，在必要的时候需提醒用户到院就医，谨遵医嘱。"),
#         # HumanMessage(content="你是谁？简要回答")
#         messages=[{'role': 'system', 'content': '你是四川华西医院的助诊助手，请为用户解答问题，在必要的时候需提醒用户到院就医，谨遵医嘱。'},
#                   {'role': 'user', 'content': '你好，我是lucy。你是谁？简要回答'}],
#         stream=True,
#         # 展示token使用信息
#         stream_options={"include_usage": True}
#     )
#
#     for chunk in completion:
#         if chunk.choices and chunk.choices[0].delta.content:
#             print(chunk.choices[0].delta.content, end="", flush=True)
#         if chunk.usage:
#             print(f"\n\nToken 使用信息：{chunk.usage}")
#
# if __name__ == '__main__':
#     get_response()

model = ChatTongyi(model="qwen3-max",
                   api_key=os.getenv("DASHSCOPE_API_KEY"))
messages = [{'role': 'system',
             'content': '你是四川华西医院的助诊助手，请为用户解答问题，在必要的时候需提醒用户到院就医，谨遵医嘱。'},
            {'role': 'user', 'content': '你好，我是lucy。你是谁？简要回答'}]
res = model.stream(input(messages))
for chunk in res:
    print(chunk.content, end="", flush=True)
