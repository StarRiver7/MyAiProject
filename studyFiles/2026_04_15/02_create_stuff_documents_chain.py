# create_stuff_documents_chain:把检索到的文档拼接给模型
import os

from langchain_classic.chains.combine_documents import create_stuff_documents_chain
from langchain_core.documents import Document
from langchain_core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from pydantic import SecretStr

# 1.设置大模型
model = ChatOpenAI(
    model="qwen3-max",
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
    api_key=SecretStr(os.getenv("DASHSCOPE_API_KEY")),
    streaming=True,
    temperature=0.7)

# 2.创建链
prompt = PromptTemplate.from_template(""""
如下文档{docs}中，香蕉是什么颜色的？
""")

chain = create_stuff_documents_chain(model,prompt,document_variable_name="docs")

docs = [
    Document(
        page_content="香蕉是白色的"
    ),
    Document(
        page_content="香蕉是产自南美洲的"
    )
]

# 执行
resource = chain.invoke({"docs":docs})
print(resource)