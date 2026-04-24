# Redis基础（核心面试知识）

---

## 一、Redis概述

> Redis (Remote Dictionary Server) 是一个开源的**内存数据库**，以键值对形式存储数据

### 1.1 Redis特点

| 特点 | 说明 |
|------|------|
| 内存存储 | 速度快，适合高频读写 |
| 持久化 | 支持RDB和AOF |
| 多种数据结构 | String、Hash、List、Set、Sorted Set等 |
| 原子操作 | 支持事务 |
| 发布订阅 | 消息队列功能 |
| 主从复制 | 高可用 |
| 集群支持 | 分布式部署 |

### 1.2 Redis vs 其他缓存

| 对比 | Redis | Memcached | MongoDB |
|------|-------|-----------|---------|
| 数据结构 | 丰富 | 单一K-V | 文档 |
| 持久化 | 支持 | 不支持 | 支持 |
| 主从复制 | 支持 | 支持 | 支持 |
| 内存管理 | 支持淘汰策略 | 支持淘汰策略 | 内存映射 |
| 性能 | 极高 | 高 | 中 |

---

## 二、Redis安装与配置

### 2.1 安装方式

```bash
# Ubuntu/Debian
apt install redis-server

# CentOS/RHEL
yum install redis

# 源码安装
wget http://download.redis.io/releases/redis-7.0.0.tar.gz
tar -xzf redis-7.0.0.tar.gz
cd redis-7.0.0
make
make install
```

### 2.2 配置文件

```bash
# 配置文件位置
/etc/redis/redis.conf  # 系统安装
redis.conf             # 源码安装

# 核心配置
dir /var/lib/redis     # 数据目录
pidfile /var/run/redis.pid
port 6379
bind 127.0.0.1         # 绑定地址
requirepass your_password  # 密码
```

### 2.3 启动停止

```bash
# 启动
systemctl start redis-server
redis-server /path/to/redis.conf

# 停止
systemctl stop redis-server
redis-cli shutdown

# 查看状态
systemctl status redis-server
```

---

## 三、Redis客户端

### 3.1 redis-cli

```bash
# 连接本地
redis-cli

# 连接远程
redis-cli -h host -p port -a password

# 测试连接
redis-cli ping  # 返回 PONG

# 批量执行
echo "set key1 value1\nget key1" | redis-cli
```

### 3.2 高级客户端

| 语言 | 客户端 |
|------|--------|
| Python | redis-py |
| Java | Jedis, Lettuce |
| Node.js | ioredis |
| Go | go-redis |
| PHP | predis |

### 3.3 Python示例

```python
import redis

# 连接
r = redis.Redis(
    host='localhost',
    port=6379,
    password='password',
    db=0
)

# 操作
r.set('name', 'Redis')
r.get('name')  # b'Redis'
r.delete('name')
r.exists('name')  # 0
```

---

## 四、Redis基础命令

### 4.1 键操作

```bash
# 查看所有键
keys *
keys user:*  # 模糊匹配

# 键类型
type key

# 键存在
exists key  # 1存在，0不存在

# 键过期
expire key 60  # 60秒后过期
ttl key  # 查看剩余过期时间
persist key  # 取消过期

# 删除键
del key1 key2

# 重命名键
rename oldkey newkey
renamenx oldkey newkey  # 新键不存在才重命名
```

### 4.2 服务器操作

```bash
# 查看服务器信息
info
info memory  # 内存信息
info stats   # 统计信息

# 清空数据库
flushdb  # 当前库
flushall  # 所有库

# 查看配置
config get *
config get maxmemory

# 主从信息
info replication
```

---

## 五、Redis数据类型

| 类型 | 说明 | 示例 |
|------|------|------|
| String | 字符串 | `set name "Redis"` |
| Hash | 哈希表 | `hset user:1 name "Tom"` |
| List | 列表 | `lpush list1 "a" "b" "c"` |
| Set | 集合 | `sadd set1 "a" "b" "c"` |
| Sorted Set | 有序集合 | `zadd zset1 1 "a" 2 "b"` |
| Bitmap | 位图 | `setbit bitmap1 0 1` |
| HyperLogLog | 基数统计 | `pfadd hll1 "a" "b" "c"` |
| Geospatial | 地理位置 | `geoadd city 116.40 39.90 "Beijing"` |

---

## 六、Redis内存管理

### 6.1 内存使用

```bash
# 查看内存使用
info memory

# 内存配置
maxmemory 1GB  # 最大内存
maxmemory-policy allkeys-lru  # 内存淘汰策略
```

### 6.2 内存淘汰策略

| 策略 | 说明 |
|------|------|
| noeviction | 不淘汰，报错 |
| allkeys-lru | 所有键LRU |
| volatile-lru | 有过期时间的键LRU |
| allkeys-random | 随机删除所有键 |
| volatile-random | 随机删除有过期时间的键 |
| volatile-ttl | 删除TTL最小的键 |
| allkeys-lfu | 所有键LFU（4.0+） |
| volatile-lfu | 有过期时间的键LFU（4.0+） |

### 6.3 内存优化

```
1. 合理设置maxmemory
2. 选择合适的淘汰策略
3. 定期清理过期键
4. 使用数据结构优化（如Hash存储对象）
5. 避免大键
```

---

## 七、Redis性能测试

```bash
# 性能测试
redis-benchmark -h host -p port -c 50 -n 100000

# 测试SET操作
redis-benchmark -t set -n 100000 -q

# 测试GET操作
redis-benchmark -t get -n 100000 -q

# 测试多种操作
redis-benchmark -t set,get,incr,lpush,lpop -n 100000 -q
```

---

## 八、重要背点总结

> **面试高频考点**：
> 1. Redis特点（内存存储、持久化、多种数据结构）
> 2. Redis vs Memcached区别
> 3. 内存淘汰策略（LRU、LFU）
> 4. 基础命令（keys、expire、ttl、del）
> 5. 配置文件核心参数（port、bind、requirepass、maxmemory）
> 6. 数据类型种类（8种）
> 7. 性能测试方法（redis-benchmark）
> 8. 内存优化技巧