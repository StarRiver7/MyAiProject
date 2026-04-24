# 在 Python 中， await 关键字主要用在 async def 定义的协程函数中，用于暂停协程的执行，直到异步操作完成，然后继续执行后续代码。

import asyncio
import time


async def sub_task():
    print('sub task')
    return 100


async def task():
    # 暂停当前的 task 执行
    # 等待 sub_task 执行完毕
    result = await sub_task()
    # 再执行后续代码
    print('result:', result)


if __name__ == '__main__':
    coro = task()
    asyncio.run(coro)
# await 关键字后面可以跟 coroutine、future 对象，如果 await 的是其他类型的对象可能会出现：
# TypeError: xxx can't be used in 'await' expression

# ==========================================================================================

# 当 await 后面是协程对象时，事件循环暂停当前协程执行，然后继续执行 await 后面的协程对象中的代码， 此时是不会从 task1 切换到 task2。

import asyncio


async def task02():
    print('task02')
    return 200


async def sub_task():
    print('sub_task')
    return 100


async def task01():
    print('task01')
    result = await sub_task()
    return result


async def start():
    # 在事件循环中注册两个任务 task01 和 task02
    # 并等待两个任务的执行结果
    result = await asyncio.gather(task01(), task02())
    print(result)


if __name__ == '__main__':
    asyncio.run(start())
# task01
# sub_task
# task02
# [100, 200]

# ==========================================================================================

# 但是，当 await 后面的对象换成了 future 对象，则事件循环会挂起当前任务，并转到其他的任务去执行。我们也可以理解为，await future 时，就是事件循环切换任务的一个时机。请看下面的示例代码：

import asyncio


async def task02():
    print('task02')
    return 200


async def sub_task():
    print('sub_task')
    return 100


async def task01():
    print('task01')
    # 注意下面的代码：sleep 内部会执行 await future，此时任务会切换到任务2去执行
    await asyncio.sleep(3)
    result = await sub_task()
    return result


async def start():
    result = await asyncio.gather(task01(), task02())
    print(result)


if __name__ == '__main__':
    asyncio.run(start())
# task01
# task02
# sub_task
# [100, 200]
# 从执行结果来看，await future 时，事件循环确实从 task01 这个任务线切换到了 task02 这个任务线上。
