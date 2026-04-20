# 如何设计Memory模块？
# 1.最直接：保留一个聊天消息列表
# 2.简单的新思路：只返回最近交互的k条消息
# 3.返回过去k条消息的简介摘要
# 4.从存储的消息中提取实体，并且仅返回有关当前运行中引用的实例的消息

# 1.ChatMessageHistory：消息列表
# 2.ConversationBufferMemory：完整保存所有历史消息
# 3.Window Memory：只保留最近 k 轮
# 4.Summary Memory：把历史对话压缩成摘要
# 5.TokenBufferMemory：按 token 数量控制上下文
# 6.TokenBufferMemory：按 token 数量控制上下文