# 使用 asyncio 的 Python 并发

https://www.manning.com/books/python-concurrency-with-asyncio

## 第二章 asyncio 基础

### 本章涵盖

1. 异步 await 语法和协程的基础知识。
2. 同时运行协程和任务。
3. 取消任务。
4. 手动创建事件循环。
5. 测量协程的执行时间。

我们将更多地了解 coroutine 构造以及如何使用 async await 语法来定义和运行协程。我们还将通过使用任务来检查如何并发运行协程，并通过创建可重用的计时器来检查我们通过并发运行所节省的时间。最后，我们将研究软件工程师在使用 asyncio 时可能犯的常见错误以及如何使用调试模式来发现这些问题。

### 2.1 介绍协程

想象一个协程就像一个普通的 Python 函数，但是当它遇到一个可能要花一点时间才能完成的操作时，它可以暂停执行。当这个长时间运行的操作完成时，我们可以恢复我们暂停的协程，并完成协程中的任何其他代码的执行。当一个暂停的协程正在等待它暂停的操作完成时，我们可以运行其他代码。

要创建和暂停协程，我们需要学习使用 Python 的 async 和 await 关键字。async 关键字让我们能够定义协程；await 关键字则允许我们在遇到耗时操作时暂停协程。

### 2.1.1 使用 async 关键字创建协程

创建协程非常简单，与创建普通 Python 函数没有太大区别。唯一的区别是，我们使用 async def 代替 def 关键字。async 关键字将函数标记为协程，而不是普通 Python 函数。

#### Listing2.1 使用 async 关键字

```python
async def my_coroutine() -> None:
    print('Hello World!')
```

值得注意的是，这个协程没有执行任何长时间运行的操作。

#### Listing2.2 将协程与普通函数进行比较

```python
async def coroutine_add_one(number: int) -> int:
    return number + 1

def add_one(number: int) -> int:
    return number + 1

function_result = add_one(1)
coroutine_result = coroutine_add_one(1)

print(f'Function result is {function_result} and the type is {type(function_result)}')
print(f'Coroutine result is {coroutine_result} and the type is {type(coroutine_result)}')
```

请注意，当我们调用正常的 add_one 函数时，它会立即执行并返回我们期望的结果，即另一个整数。但是，当我们调用 coroutine_add_one 时，我们根本不会执行 coroutine 中的代码。我们得到的是一个 coroutine 对象。这是一个重要的问题，因为当我们直接调用协程时，它们不会被执行。相反，我们创建一个可以稍后运行的协程对象。要运行协程，我们需要显式地在事件循环上运行它。如果还没有事件循环，我们需要创建一个事件循环。

#### Listing2.3 运行协程

```python
import asyncio

async def coroutine_add_one(number: int) -> int:
    return number + 1

result = asyncio.run(coroutine_add_one(1))
print(result)
```

在这个场景中，asyncio.run 执行了几个重要的操作。首先，它会创建一个全新的事件循环。成功创建后，它会接收我们传入的协程并运行直至完成，然后返回结果。该函数还会在主协程结束后清理所有可能仍在运行的内容。所有操作完成后，它会关闭并终止事件循环。

### 2.1.2 使用 await 关键字暂停执行

asyncio 的真正优势在于能够在遇到耗时操作时暂停执行，让事件循环在此期间运行其他任务。要暂停执行，我们使用 await 关键字。await 关键字通常后跟一个协程调用（更准确地说，是一个被称为 awaitable 的实例，它不一定是协程；本章后续部分我们将进一步了解）。我们可以在 coroutine 调用前使用 await 关键字。扩展我们之前的程序，我们可以编写一个程序，在 “main” 异步函数中调用 add_one 函数并获取结果。

#### Listing2.4 使用 await 等待协程的结果

```python
import asyncio

async def add_one(number: int) -> int:
    return number + 1

async def main() -> None:
    one_plus_one = await add_one(1)  
    two_plus_one = await add_one(2) 

    print(one_plus_one)
    print(two_plus_one)

asyncio.run(main())
```

当我们遇到一个 await 表达式时，我们暂停父协程并运行 await 表达式中的协程。一旦它完成，我们恢复父协程并分配返回值。我们暂停了两次执行。我们首先等待 add_one(1) 的调用。一旦我们得到了结果，主函数就会开始执行，我们将把 add_one(1) 的返回值分配给变量 one_plus_one，在这个例子中就是 2。然后，我们为 add_one(2) 做同样的事情，然后打印结果。

目前来看，这段代码的运行方式与普通的顺序代码并无不同。实际上，我们只是在模拟正常的调用栈。接下来，让我们通过一个简单的示例来了解如何在等待期间通过模拟休眠操作来执行其他代码。

### 2.2 通过 sleep 引入长时间运行的协程

我们可以使用 asyncio.sleep 让协程“休眠”指定的秒数。这样就能让我们的协程暂停相应的时间，从而模拟出调用数据库或 Web API 等耗时较长的操作时的情况。让我们来看一个简单的例子，如下面的代码所示：该代码会休眠 1 秒钟，然后打印出“Hello World!”消息。

#### Listing2.5 使用 sleep 函数的首个应用程序

```python
import asyncio

async def hello_world_message() -> str:
    await asyncio.sleep(1)
    return 'Hello World'

async def main() -> None:
    message = hello_world_message()
    print(message)

asyncio.run(main())
```

当我们运行这个应用程序时，程序会等待 1 秒钟后再输出“Hello World!”这条消息。由于 hello_world_messages 是一个协程，并且我们使用 asyncio.sleep 让它暂停了 1 秒钟，因此在这段时间内，程序可以同时执行其他代码。

#### Listing2.6 可重用的延迟函数

```python
import asyncio

async def delay(delay_seconds: int) -> int:
    print(f'sleeping for {delay_seconds} second(s)')
    await asyncio.sleep(delay_seconds)
    print(f'finished sleeping for {delay_seconds} second(s)')
    return delay_seconds
```

该函数接受一个以秒为单位的整数参数，表示函数需要休眠的时间长度。当休眠结束后，函数会将该整数值返回给调用者。同时，函数还会输出休眠的开始和结束时间，这有助于我们了解在协程暂停期间是否有其他代码在并发执行。