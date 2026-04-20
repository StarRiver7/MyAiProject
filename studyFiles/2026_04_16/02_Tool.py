# Tools本质上是封装了特定功能的可调用模块，是Agent、Chain或LLM可以与世界交互的接口

# Tool通常包括以下要素：
# 1. name：Tool的名称，用于在Agent的提示中标识
# 2. description：Tool的描述，用于向用户解释Tool的功能
# 3. 该工具输入的Json模式
# 4. 函数：Tool所调用的函数，该函数定义了Tool的具体功能
# 5. return_direct：布尔值，表示是否直接返回Tool的输出，还是等待Agent的进一步处理

# 两种自定义工具：
# 1. 使用@Tool装饰器：装饰器默认使用函数名称作为工具名称，但可以通过参数name_or_callable来覆盖此设置。
#    装饰器将使用函数的文档字符串作为工具的描述，因此函数必须提供文档字符串。
# 2. 使用StructuredTool.from_function类方法：类似@tool修饰器，但允许更多配置和同步/异步实现的规范。

# 属性
# name：必选的，在提供给LLM或Agent的工具集中必须是唯一的。
# description：可选但建议，描述工具的功能。LLM或Agent将使用此描述作为上下文，使用它确定工具的使用。
# args_schema：可选但建议，可用于提供更多信息(例如，few-shot示例)或验证预期参数。
# return_direct：仅对Agent相关。当为True时，在调用给定工具后，Agent将停止并将结果直接返回给用户。
from langchain_core.tools import tool, StructuredTool

# 设置大模型：
# ......

@tool
def add_number(a:int,b:int)->int:
    """计算两个整数的和"""
    return a + b

print(f"name: {add_number.name}")
print(f"description: {add_number.description}")
print(f"args_schema: {add_number.args_schema}")
print(f"return_direct: {add_number.return_direct}")

# 调用：
add_number.invoke(1,2)


# 使用StructuredTool：
def search_google(query:str):
    return "返回的内容"

search = StructuredTool.from_function(
    func = search_google,
    name = "search",
    description = "search google for the query",
)

print(f"name: {search.name}")
print(f"description: {search.description}")
print(f"args_schema: {search.args_schema}")
print(f"return_direct: {search.return_direct}")








