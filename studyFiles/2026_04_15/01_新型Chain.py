import os

from langchain_openai import ChatOpenAI
from langchain_classic.chains.sql_database.query import create_sql_query_chain
from langchain_community.utilities import SQLDatabase
from pydantic import SecretStr

# 安装命令：pip install pymysql
#           create_sql_query_chain              SQLDatabaseChain
# 功能	    自然语言查询 → 生成 SQL → 执行查询	    自然语言查询 → 生成 SQL
# 数据库执行  自动执行 SQL 查询并返回结果             仅生成 SQL 查询，不执行

# create_Sql_Query_Chain的使用
# 1.设置数据库连接
# 格式：mysql+pymysql://用户名:密码@host主机:端口/数据库名
db = SQLDatabase.from_uri("mysql+pymysql://root:123456@localhost:3306/ai")

# 2.设置大模型
model = ChatOpenAI(
    model="qwen3-max",
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
    api_key=SecretStr(os.getenv("DASHSCOPE_API_KEY")),
    streaming=True,
    temperature=0.7)

# 3.Sql语句判断方法
def execute_sql(query):
    # 判断 SQL 语句是否以 SELECT 开头，忽略大小写
    if not query.strip().lower().startswith("select"):
        # 拒绝非 SELECT 类型的查询
        raise ValueError("Only SELECT queries are allowed.")

    # 继续执行 SQL 查询的逻辑（比如通过数据库执行）
    print(f"Executing query: {query}")
    # 例如数据库操作：
    # result = db.execute(query)
    # return result
    return "Query executed successfully"

# 4.chain调用
chain = create_sql_query_chain(model, db)

response = chain.invoke({"question":"删除user表"})

# 示例：拒绝非 SELECT 查询
try:
    result = execute_sql(response)
    print(result)
except ValueError as e:
    print(f"Error: {e}")


# SQLDatabaseChain的使用
# 注意：需要先安装 langchain-experimental：pip install langchain-experimental
from langchain_experimental.sql import SQLDatabaseChain

# 先查看数据库中有哪些表和字段
print("\n📊 数据库信息：")
print(f"数据库类型: {db.dialect}")
print(f"可用的表: {db.get_usable_table_names()}")

# 创建 SQLDatabaseChain（需要传入大模型和数据库连接）
# verbose=True 会显示完整的执行过程（生成的SQL、中间步骤等）
db_chain = SQLDatabaseChain.from_llm(model, db, verbose=True)

# 示例1：简单查询
print("\n【示例1】简单查询")
print("-" * 60)
question1 = "查询user表中的所有数据，只显示前5条"
print(f"📝 自然语言问题: {question1}")
print("🔄 执行中...")
response1 = db_chain.run(question1)
print(f"✅ 查询结果: {response1}")

# 示例2：带条件的查询（使用实际存在的字段）
print("\n【示例2】带条件的查询")
print("-" * 60)
question2 = "查询user表中的所有记录，按ID排序"
print(f"📝 自然语言问题: {question2}")
print("🔄 执行中...")
response2 = db_chain.run(question2)
print(f"✅ 查询结果: {response2}")

