
# =====================================================
# 2026.4.11 - LangChain 完整学习记录
# =====================================================

"""
一、LangChain 基础核心
-------------------
1. PromptTemplate（提示词模板）
   - 核心思想：固定模板 + 动态变量
   - 创建方式：PromptTemplate(template=..., input_variables=[...])
   - partial_variables：设置默认值，格式化前预先填充
   - format() / format_messages()：填充变量生成完整提示词

2. ChatPromptTemplate（聊天提示词模板）
   - 支持多角色对话：system（系统）、human（用户）、ai（助手）
   - 创建方式1：from_messages([("system", "..."), ("human", "...")])
   - 创建方式2：组合 SystemMessagePromptTemplate + HumanMessagePromptTemplate
   - 适用场景：需要明确角色分工的对话场景

二、大模型调用与输出解析
-------------------
1. ChatOpenAI 配置
   - model：指定模型名称（如 qwen3-max）
   - base_url：API 接口地址
   - api_key：使用 SecretStr 安全封装
   - temperature：控制创造性（0-2，越高越随机）
   - streaming=True：开启流式输出

2. 输出解析器（Output Parsers）
   (1) StrOutputParser：将模型响应转为纯字符串
   (2) CommaSeparatedListOutputParser：解析逗号分隔字符串为列表
       - get_format_instructions()：获取格式指令注入提示词
   (3) JsonOutputParser：解析 JSON 字符串为 Python 字典
       - 需在提示词中明确要求返回 JSON 格式
   (4) PydanticOutputParser：基于 Pydantic 模型的结构化解析
       - 定义 BaseModel 约束输出结构
       - 自动校验类型和字段约束

三、LCEL（LangChain Expression Language）链式表达式
-------------------
1. 管道符 | 串联组件
   chain = prompt | model | parser

2. 执行流程
   prompt（填充变量）→ model（调用大模型）→ parser（解析结果）

3. 调用方式
   - invoke()：同步调用，等待完整结果
   - stream()：流式输出，逐 token 返回

四、Pydantic 数据建模与校验
-------------------
1. 基础用法
   - 继承 BaseModel 定义数据模型
   - 字段类型注解：str, int, float, list[str] 等
   - 必填字段：无默认值
   - 可选字段：field: str | None = None

2. Field 约束
   - Field(..., title="说明")：必填字段
   - Field(default, ge=0, le=100)：数值范围约束
   - Field(..., min_length=1, max_length=10)：字符串长度约束
   - HttpUrl：URL 格式校验

3. 自定义校验器
   @field_validator("字段名")
   def validator(cls, v):
       if 不满足条件:
           raise ValueError("错误信息")
       return v  # 可返回格式化后的值

4. 序列化/反序列化
   - model_validate_json(json_str)：从 JSON 字符串解析
   - model_dump()：转为 Python 字典
   - model_dump_json()：转为 JSON 字符串

5. 嵌套模型
   class Address(BaseModel):
       city: str
   class User(BaseModel):
       address: Address  # 嵌套其他模型

五、结构化信息提取实战
-------------------
1. PydanticOutputParser 工作流
   (1) 定义 Pydantic 模型约束输出结构
   (2) 创建解析器：PydanticOutputParser(pydantic_object=Model)
   (3) 获取格式指令：parser.get_format_instructions()
   (4) 注入提示词：prompt.partial(format_instructions=...)
   (5) 构建链：chain = prompt | model | parser
   (6) 调用提取：response = chain.invoke({"input": "文本"})

2. 应用场景
   - 用户信息提取（姓名、年龄、爱好）
   - 情感分析（情感倾向、置信度、关键词）
   - 实体识别、关键信息抽取

六、容错机制
-------------------
1. OutputFixingParser（输出修复解析器）
   - 作用：自动修复大模型输出的格式错误
   - 工作流程：
     ① 原始解析器尝试解析 → 失败
     ② 将错误信息 + 错误输出 + 格式要求发送给大模型
     ③ 大模型修正格式后返回
     ④ 原始解析器再次解析
     ⑤ 重复最多 max_retries 次

   - 使用方式：
     fixing_parser = OutputFixingParser.from_llm(
         parser=parser,
         llm=model,
         max_retries=3
     )
     fixed_data = fixing_parser.parse(misformatted_output)

   - 适用场景：单引号、字段缺失、多余文本等格式问题
   - 不适用：内容逻辑错误、网络调用失败

2. 兜底方案
   try:
       result = fixing_parser.parse(output)
   except Exception:
       fallback = Model(name="未知", field=[])  # 默认值

七、Python 类型注解（Type Hints）
-------------------
1. 基本类型
   - int, str, float, bool, bytes

2. 容器类型
   - List[int]：整数列表
   - Dict[str, int]：键值对字典
   - Tuple[int, int]：固定长度元组
   - Set[str]：字符串集合

3. 特殊类型
   - Union[str, int]：多种类型之一
   - Optional[str]：可选类型（等价于 Union[str, None]）
   - Any：任意类型
   - Literal["GET", "POST"]：字面量限定

4. 泛型
   T = TypeVar('T')  # 无约束泛型
   Num = TypeVar('Num', int, float)  # 有约束泛型

   def add(a: Num, b: Num) -> Num:
       return a + b

5. 自定义类型
   UserId = NewType('UserId', int)  # 逻辑隔离的类型别名

"""
