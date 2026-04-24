# 虽然这听起来很简单，但要正确地管理任务的挂起和恢复时机，需要一套专门的调度机制。幸运的是，Python内置的asyncio模块，正好为我们提供了这样的能力--事件循环(Event Loop)
# 它的工作流程大致是这样的:
# 首先，创建一个事件循环
# 然后，将需要执行的任务注册到事件循环中
# 最后,启动事件循环，开始调度和执行各个任务

# 需要注意的是，为了让事件循环正确地识别和调度任务，我们需要遵循以下两个规则:
# 在任务函数定义时，需要使用asyncdef定义，表示这是一个异步函数，是需要交给事件循环管理的
# 在任务函数内部，当遇到需要等待其他异步操作的地方，需要使用await。这就告诉事件循环：此处可以挂起当前任务，等异步操作完成后再恢复执行。这样可以避免程序在等待期间白白占用资源，从而提升整体效率。
import asyncio
import time


async def task1():
    print('task1 开始执行')
    # await 后面的对象必须是 async def 定义的对象，而 sleep 则不是，所以会报错
    # await time.sleep(5)
    # 需要切换为 async def 版本的 sleep 函数
    await asyncio.sleep(5)
    print('task1 结束执行')
    return 10

async def task2():
    print('task2 开始执行')
    # await time.sleep(5)
    await asyncio.sleep(3)
    print('task2 结束执行')
    return 20


# 任务执行入口点
async def main():
    print('main 开始执行')
    # 获得事件循环
    event_loop = asyncio.get_running_loop()
    # 手动注册任务
    t1 = event_loop.create_task(task1())
    t2 = event_loop.create_task(task2())

    # 等待事件循环调度执行、获得 t1 任务的结果
    result = await t1
    print('任务1执行结果:', result)

    # 等待事件循环调度执行、获得 t2 任务的结果
    result = await t2
    print('任务2执行结果:', result)

    print('main 结束执行')


if __name__ == '__main__':
    start = time.time()
    # 创建事件循环
    event_loop = asyncio.get_event_loop()
    # 启动事件循环
    event_loop.run_until_complete(main())
    print(time.time() - start)