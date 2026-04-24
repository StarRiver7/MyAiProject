# SQL基础（核心面试知识）

---

## 一、SQL语句分类

| 类别 | 作用 | 关键字 |
|------|------|--------|
| DDL | 定义数据库对象 | CREATE、DROP、ALTER |
| DML | 操作数据 | INSERT、UPDATE、DELETE |
| DQL | 查询数据 | SELECT |
| DCL | 控制权限 | GRANT、REVOKE |

---

## 二、SELECT执行顺序（高频面试点）

> 面试必问：写出SELECT语句的执行顺序

```
1. FROM          -- 确定数据来源
2. ON            -- 连接条件
3. JOIN          -- 关联表
4. WHERE         -- 筛选条件
5. GROUP BY      -- 分组
6. HAVING        -- 分组后筛选
7. SELECT        -- 选择字段
8. DISTINCT      -- 去重
9. ORDER BY      -- 排序
10. LIMIT        -- 限制条数
```

**记忆口诀**：F O J W G H S D O L（佛祖救我哥好三弟哦）

---

## 三、WHERE与HAVING的区别

| 对比项 | WHERE | HAVING |
|--------|-------|--------|
| 执行顺序 | 分组前筛选 | 分组后筛选 |
| 使用场景 | 筛选原始数据 | 筛选聚合结果 |
| 能否用聚合函数 | 不能 | 能 |

```sql
-- WHERE：筛选分组前的原始数据
SELECT * FROM employee WHERE salary > 5000;

-- HAVING：筛选分组后的聚合结果
SELECT department, COUNT(*) as cnt 
FROM employee 
GROUP BY department 
HAVING cnt > 10;
```

---

## 四、JOIN连接（必须掌握）

### 4.1 七种JOIN写法

```sql
-- 1. INNER JOIN：只保留两表交集
SELECT * FROM A INNER JOIN B ON A.id = B.id;

-- 2. LEFT JOIN：保留A全部 + B匹配部分
SELECT * FROM A LEFT JOIN B ON A.id = B.id;

-- 3. RIGHT JOIN：保留B全部 + A匹配部分
SELECT * FROM A RIGHT JOIN B ON A.id = B.id;

-- 4. FULL OUTER JOIN：AB全部（MySQL不支持，用UNION实现）
SELECT * FROM A LEFT JOIN B ON A.id = B.id
UNION
SELECT * FROM A RIGHT JOIN B ON A.id = B.id;

-- 5. LEFT JOIN + WHERE B.id IS NULL：只在A中
SELECT * FROM A LEFT JOIN B ON A.id = B.id WHERE B.id IS NULL;

-- 6. RIGHT JOIN + WHERE A.id IS NULL：只在B中
SELECT * FROM A RIGHT JOIN B ON A.id = B.id WHERE A.id IS NULL;

-- 7. FULL OUTER JOIN + WHERE：一左一右排除交集
SELECT * FROM A LEFT JOIN B ON A.id = B.id WHERE B.id IS NULL
UNION
SELECT * FROM A RIGHT JOIN B ON A.id = B.id WHERE A.id IS NULL;
```

### 4.2 图解记忆

```
INNER      ：A ∩ B
LEFT       ：A 全部
RIGHT      ：B 全部
FULL       ：A ∪ B
LEFT NOT   ：A - B
RIGHT NOT  ：B - A
FULL NOT   ：(A - B) ∪ (B - A)
```

---

## 五、GROUP BY详解

### 5.1 特点
- GROUP BY后可以跟多个字段，表示多级分组
- SELECT后的字段必须是GROUP BY后的字段或聚合函数

### 5.2 常用聚合函数

| 函数 | 作用 |
|------|------|
| COUNT() | 计数 |
| SUM() | 求和 |
| AVG() | 平均值 |
| MAX() | 最大值 |
| MIN() | 最小值 |

---

## 六、子查询

### 6.1 标量子查询
返回单个值

```sql
SELECT * FROM employee 
WHERE salary > (SELECT AVG(salary) FROM employee);
```

### 6.2 列子查询
返回一列多行

```sql
SELECT * FROM employee 
WHERE department_id IN 
(SELECT department_id FROM department WHERE name LIKE '%技术%');
```

### 6.3 行子查询
返回一行多列

```sql
SELECT * FROM employee 
WHERE (salary, age) = (SELECT MAX(salary), MAX(age) FROM employee);
```

### 6.4 表子查询
返回临时表

```sql
SELECT * FROM 
(SELECT * FROM employee WHERE salary > 5000) AS t;
```

---

## 七、常用函数（高频）

### 7.1 字符串函数

```sql
CONCAT(str1, str2, ...)     -- 拼接字符串
SUBSTRING(str, start, len)  -- 截取字符串
UPPER(str) / LOWER(str)     -- 转大小写
TRIM(str)                   -- 去除首尾空格
LENGTH(str)                 -- 获取字节长度
CHAR_LENGTH(str)            -- 获取字符长度
```

### 7.2 日期函数

```sql
NOW() / SYSDATE()           -- 当前日期时间
CURDATE()                   -- 当前日期
CURTIME()                   -- 当前时间
DATE_FORMAT(date, format)   -- 格式化日期
DATE_ADD(date, INTERVAL n DAY)  -- 日期加
DATEDIFF(date1, date2)      -- 日期差
YEAR/MONTH/DAY(date)        -- 提取年月日
```

### 7.3 条件函数

```sql
-- IF(expr1, expr2, expr3)：三元表达式
SELECT IF(salary > 5000, '高', '低') FROM employee;

-- IFNULL(expr1, expr2)：NULL替换
SELECT IFNULL(bonus, 0) FROM employee;

-- CASE WHEN：多条件判断
SELECT CASE 
    WHEN salary > 10000 THEN '高'
    WHEN salary > 5000 THEN '中'
    ELSE '低'
END FROM employee;
```

---

## 八、窗口函数（MySQL 8.0+ 高频面试点）

### 8.1 窗口函数分类

```sql
-- 1. 聚合窗口函数
SUM() OVER()
AVG() OVER()
COUNT() OVER()
MAX() OVER()
MIN() OVER()

-- 2. 排序窗口函数
ROW_NUMBER() OVER()  -- 1,2,3,4（无并列）
RANK() OVER()        -- 1,1,3,4（有并列跳序）
DENSE_RANK() OVER()   -- 1,1,2,3（有并列不跳序）

-- 3. 取值窗口函数
LEAD(col, n) OVER()   -- 下一行
LAG(col, n) OVER()    -- 上一行
FIRST_VALUE(col) OVER()  -- 第一值
LAST_VALUE(col) OVER()   -- 最后值
```

### 8.2 OVER子句详解

```sql
-- 不指定窗口范围：默认整个分区
SUM(salary) OVER(PARTITION BY department)

-- 指定窗口范围：当前行 + 前N行
SUM(salary) OVER(PARTITION BY department ORDER BY salary 
                 ROWS BETWEEN 2 PRECEDING AND CURRENT ROW)

-- 关键关键字
ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW  -- 第一行到当前行
ROWS BETWEEN CURRENT ROW AND UNBOUNDED FOLLOWING  -- 当前行到最后一行
ROWS BETWEEN 1 PRECEDING AND 1 FOLLOWING         -- 前一行到后一行
```

### 8.3 经典面试题：分组后每组TopN

```sql
-- 方法：窗口函数 + 子查询
SELECT * FROM (
    SELECT *, 
           ROW_NUMBER() OVER(PARTITION BY department ORDER BY salary DESC) as rn
    FROM employee
) t WHERE rn <= 3;
```

---

## 九、UNION与UNION ALL

| 对比项 | UNION | UNION ALL |
|--------|-------|-----------|
| 去重 | 去重 | 不去重 |
| 性能 | 较慢 | 较快 |
| 排序 | 会对相同行去重 | 保留所有 |

---

## 十、重要背点总结

> **面试高频考点**：
> 1. SELECT执行顺序（十步骤）
> 2. 七种JOIN写法（图解）
> 3. WHERE vs HAVING
> 4. 窗口函数（ROW_NUMBER、RANK、DENSE_RANK）
> 5. 分组后TopN问题
> 6. 子查询分类（标量、列、行、表）