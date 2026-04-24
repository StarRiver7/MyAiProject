# SQL优化（核心面试知识）

---

## 一、SQL优化步骤

### 1.1 优化流程

```
1. 定位慢SQL
   ↓
2. 分析执行计划（EXPLAIN）
   ↓
3. 检查索引
   ↓
4. 分析优化建议
   ↓
5. 验证优化效果
```

### 1.2 定位慢SQL

```sql
-- 开启慢查询日志
SHOW VARIABLES LIKE 'slow_query%';
SHOW VARIABLES LIKE 'long_query_time%';

-- 设置慢查询阈值（秒）
SET GLOBAL slow_query_log = 'ON';
SET GLOBAL long_query_time = 1;

-- 查看慢查询日志位置
SHOW VARIABLES LIKE 'slow_query_log_file';

-- 实时查看慢查询
SHOW PROCESSLIST;
```

---

## 二、EXPLAIN执行计划（高频面试点）

### 2.1 使用方法

```sql
EXPLAIN SQL语句;
EXPLAIN ANALYZE SQL语句;  -- MySQL 8.0+ 显示实际执行时间
```

### 2.2 关键字段解析

| 字段 | 说明 | 重点关注 |
|------|------|----------|
| **id** | SELECT序列号 | id越大越先执行 |
| **select_type** | 查询类型 | SIMPLE/PRIMARY/SUBQUERY/DERIVED等 |
| **type** | 访问类型 | 性能：ALL<index<range<ref<eq_ref<const |
| **possible_keys** | 可能用到的索引 | 显示可能被使用的索引 |
| **key** | 实际使用的索引 | 重点：NULL表示没使用索引 |
| **key_len** | 索引长度 | 越长越精确 |
| **rows** | 扫描行数 | 越大越不好 |
| **Extra** | 额外信息 | Using filesort/Using temporary等 |

### 2.3 type访问类型详解

| 类型 | 说明 | 性能 |
|------|------|------|
| ALL | 全表扫描 | 最差 |
| index | 全索引扫描 | 较差 |
| range | 索引范围扫描 | 中等 |
| ref | 非唯一索引等值查询 | 良好 |
| eq_ref | 唯一索引等值查询 | 优秀 |
| const/system | 单表常量查询 | 最优 |

### 2.4 Extra重要信息

```
Using filesort：
- 无法利用索引排序
- 需要额外排序操作
- 性能差，需要优化

Using temporary：
- 需要创建临时表
- 性能差，需要优化

Using index（覆盖索引）：
- 直接从索引返回数据
- 不需要回表
- 性能好

Using index condition（索引下推）：
- 利用索引筛选数据
- 减少回表次数

Using where：
- 使用WHERE过滤
- 正常情况

Using join buffer：
- 使用连接缓存
- 性能差
```

---

## 三、索引优化（高频面试点）

### 3.1 避免索引失效

```sql
-- 1. 避免函数/运算
SELECT * FROM user WHERE YEAR(create_time) = 2024;  -- 失效
SELECT * FROM user WHERE create_time >= '2024-01-01' AND create_time < '2025-01-01';  -- 有效

-- 2. 避免隐式类型转换
SELECT * FROM user WHERE phone = 13800138000;  -- 失效（phone是varchar）
SELECT * FROM user WHERE phone = '13800138000';  -- 有效

-- 3. LIKE注意事项
SELECT * FROM user WHERE name LIKE '%张%';   -- 失效
SELECT * FROM user WHERE name LIKE '张%';    -- 有效

-- 4. OR条件优化
SELECT * FROM user WHERE name = '张三' OR age = 25;  -- 可能失效
-- 改写为UNION：
SELECT * FROM user WHERE name = '张三'
UNION ALL
SELECT * FROM user WHERE age = 25 AND name != '张三';

-- 5. 复合索引最左前缀
-- 索引 idx(name, age, salary)
SELECT * FROM user WHERE name = '张三';           -- √
SELECT * FROM user WHERE name = '张三' AND age = 25;  -- √
SELECT * FROM user WHERE age = 25;                  -- ×
```

### 3.2 复合索引设计原则

```
原则1：区分度高的列放前面
原则2：查询条件包含的列放索引
原则3：复合索引覆盖更多查询
原则4：避免冗余索引
```

---

## 四、SQL写法优化

### 4.1 SELECT优化

```sql
-- 避免SELECT *
SELECT id, name, age FROM user;  -- 只查需要的字段

-- 避免 DISTINCT +
SELECT DISTINCT id FROM user;  -- 改为GROUP BY
SELECT id FROM user GROUP BY id;

-- 避免COUNT(*)
SELECT COUNT(1) FROM user;  -- 用主键或常量计数
SELECT COUNT(id) FROM user;
```

### 4.2 JOIN优化

```sql
-- 小表驱动大表
-- 原则：小表（结果集小）放左边

-- B表100条，A表10000条
SELECT * FROM A JOIN B ON A.id = B.a_id;
-- A先查10000条，然后每条去B中查找（100次）

SELECT * FROM B JOIN A ON A.id = B.a_id;
-- B先查100条，然后每条去A中查找（10000次）

-- 优化：小的放左边
SELECT * FROM B JOIN A ON A.id = B.a_id;  -- B是小表
```

### 4.3 子查询优化

```sql
-- IN子查询优化
-- 改写为JOIN
SELECT * FROM user WHERE id IN (SELECT user_id FROM order);

-- 改为JOIN
SELECT DISTINCT u.* FROM user u JOIN order o ON u.id = o.user_id;
```

### 4.4 LIMIT优化

```sql
-- 分页深度分页问题
SELECT * FROM user ORDER BY id LIMIT 1000000, 10;

-- 优化1：利用主键索引
SELECT * FROM user WHERE id > 1000000 LIMIT 10;

-- 优化2：记录上次位置
SELECT * FROM user WHERE id > last_id LIMIT 10;

-- 优化3：延迟关联
SELECT u.* FROM user u 
JOIN (SELECT id FROM user ORDER BY id LIMIT 1000000, 10) t 
ON u.id = t.id;
```

---

## 五、数据库表设计优化

### 5.1 字段类型选择

```
原则1：越小越好
原则2：简单越好
原则3：避免NULL

常用类型：
- 整数：TINYINT < SMALLINT < INT < BIGINT
- 字符串：CHAR（定长）< VARCHAR（变长）
- 时间：DATE < DATETIME < TIMESTAMP
- 金额：DECIMAL（避免浮点）
```

### 5.2 字段属性

```sql
-- 避免使用TEXT/BLOB
-- 如必须使用，拆分到单独表

-- 主键设计
- 整型自增主键（InnoDB推荐）
- UUID主键（需要转换）
```

---

## 六、配置优化

### 6.1 关键参数

```sql
-- 连接相关
max_connections          -- 最大连接数
wait_timeout             -- 等待超时

-- 缓存相关
innodb_buffer_pool_size  -- InnoDB缓冲池大小（建议75%内存）
key_buffer_size          -- MyISAM索引缓存
query_cache_size         -- 查询缓存（MySQL 8.0已移除）

-- 日志相关
innodb_log_file_size     -- 日志文件大小
innodb_flush_log_at_trx_commit -- 刷盘策略

-- 临时表
tmp_table_size           -- 内存临时表大小
max_heap_table_size      -- MEMORY表大小
```

### 6.2 缓冲池优化

```sql
-- 查看缓冲池大小
SHOW VARIABLES LIKE 'innodb_buffer_pool_size';

-- 设置缓冲池大小（建议操作系统内存的75%）
SET GLOBAL innodb_buffer_pool_size = 2147483648;  -- 2GB

-- 缓冲池实例（多核CPU）
innodb_buffer_pool_instances = 4
```

---

## 七、慢查询分析

### 7.1 分析工具

```sql
-- 开启慢查询日志后，用mysqldumpslow分析
mysqldumpslow -s t -t 10 slow.log

-- 参数说明：
-s: 排序方式（c/t/l/at/al）
-t: 显示前N条

-- 使用pt-query-digest（Percona Toolkit）
pt-query-digest slow.log
```

### 7.2 分析步骤

```
1. 定位慢查询
   ↓
2. EXPLAIN分析执行计划
   ↓
3. 检查索引使用情况
   ↓
4. 分析Extra信息
   ↓
5. 优化SQL或索引
   ↓
6. 验证效果
```

---

## 八、常见优化场景

### 8.1 全表扫描优化

```sql
-- 原因：无索引、索引失效
-- 解决：创建合适索引、避免索引失效
```

### 8.2 文件排序优化

```sql
-- 原因：ORDER BY字段无索引或使用函数
-- 解决：创建索引、避免在ORDER BY中使用函数
```

### 8.3 临时表优化

```sql
-- 原因：GROUP BY字段无索引、GROUP BY + DISTINCT
-- 解决：创建索引、改写SQL
```

### 8.4 连接查询优化

```sql
-- 原因：小表未放左边、连接字段无索引
-- 解决：小表驱动大表、创建索引
```

---

## 九、重要背点总结

> **面试高频考点**：
> 1. EXPLAIN各字段含义（id/type/key/rows/Extra）
> 2. type性能排序（ALL到const）
> 3. Extra重要信息（Using filesort/Using temporary/Using index）
> 4. 索引失效的七种场景
> 5. 复合索引最左前缀原则
> 6. 小表驱动大表原则
> 7. LIMIT深度分页优化
> 8. 慢查询定位和分析流程
> 9. 连接查询优化技巧
> 10. buffer_pool配置优化