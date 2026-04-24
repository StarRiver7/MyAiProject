# async 关键字主要用于定义异步函数/协程函数，这种函数可以执行非阻塞操作（通过 await 实现），并允许在等待某些任务完成时，程序继续执行其他任务。
# 使用 async 定义异步函数/协程函数如下代码所示：

import asyncio


async def task():
    print('task')


def demo():
    coro = task()
    # <class 'coroutine'>
    print(type(coro))


if __name__ == '__main__':
    demo()
# 关于这段代码，有以下几个重要点需要理解：
#
# 协程函数的返回值不是直接的结果，而是一个 协程对象。
# 协程对象 是是一个未开始执行的任务。要执行这个任务，必须通过事件循环来调度。
import asyncio


async def task():
    print('task')


if __name__ == '__main__':
    coro = task()
    # 创建事件循环，并将 coro 协程对象注册到事件循环中，由事件循环调度运行
    asyncio.run(coro)
# Python 中的异步编程之所以需要使用协程而不是普通函数，主要是因为协程能够支持暂停和恢复执行，而普通函数则不能。
