from openai import OpenAI

client = OpenAI(
    base_url="http://localhost:11434/v1",
)

completion = client.chat.completions.create(
    model="deepseek-r1:8b",  # 您可以按需更换为其它深度思考模型
    messages = [
        {"role": "system", "content": "你是四川华西医院的就医小助手，专门为顾客提供就诊帮助,在必要的时候需要提醒患者谨遵医嘱！"},
        {"role": "user", "content": "你是谁"}
    ]
)

for chunk in completion:
    print(chunk.choices[0].delta.content, end="", flush=True)