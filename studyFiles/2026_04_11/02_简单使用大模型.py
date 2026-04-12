# 该代码功能：基于指定产品名称，调用大模型生成面向年轻人的3条吸引人广告语
# 核心技术栈：LangChain（大模型应用框架） + 通义千问模型 + Pydantic（密钥安全管理） + 输出解析

from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from pydantic import SecretStr
from langchain_core.output_parsers import StrOutputParser
import os

model = ChatOpenAI(
    model="qwen3-max", 
    base_url= "https://dashscope.aliyuncs.com/compatible-mode/v1",
    api_key=SecretStr(os.environ["DASH_SCOPE_API_KEY"]),
    temperature=0.7
)

# 创建提示词模板对象，用于标准化生成大模型的输入提示词
prompt_template = PromptTemplate(
    input_variables=["product"],  # 声明模板中需要动态传入的变量名称（此处仅需传入产品名称product）
    template="为{product}写三个吸引人的广告语，需要面向年青人",  # 固定提示词模板，{product}为变量占位符，后续将被实际产品名称替换
)

# 调用prompt_template的invoke方法，传入变量参数，生成完整的提示词对象
# 此处将product变量赋值为"HideOnBoss"，填充到模板占位符中，得到可直接传给大模型的提示词
prompt = prompt_template.invoke({"product":"可口可乐"})

# 调用大模型对象的invoke方法，传入完整提示词，发起模型调用，获取模型返回结果
# 该方法为同步调用，会等待模型返回结果后再执行后续代码
response = model.invoke(prompt)

# 注释：直接打印模型返回结果的content属性，也可获取广告语内容（与后续解析效果一致，此处注释备用）
# print(response.content)

# 实例化StrOutputParser字符串输出解析器，用于统一解析大模型返回结果为纯字符串
# 作用：屏蔽不同模型返回结果的格式差异，只提取核心文本内容
output_parser = StrOutputParser()

# 调用输出解析器的invoke方法，传入大模型返回的原始响应，解析得到纯字符串格式的广告语结果
answer = output_parser.invoke(response)

# 打印最终解析后的广告语结果
print(answer)
