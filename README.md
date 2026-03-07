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

### 1.3.3 并发性和并行性的区别
并发是指多个任务可以相互独立地发生。我们可以在只有一个核的 CPU 上实现并发，因为操作将采用抢占式多任务处理（在下一节中定义）在任务之间切换。然而，并行意味着我们必须同时执行两个或更多任务。在一台只有一个核的机器上，这是不可能的。为了使这成为可能，我们需要一个具有多个核的 CPU，可以同时运行两个任务。

虽然并行意味着并发，但并发不总是意味着并行。在多核机器上运行的多线程应用程序是并发和并行。这种设置中，我们同时运行多个任务，有两个核心独立地执行与这些任务相关联的代码。但是，通过多任务处理，我们可以同时发生多个任务，但其中只有一个在给定时间执行。

### 1.3.4 什么是多任务处理
本部分讨论了两种主要的任务处理：抢占式多任务处理和协作式多任务处理。

#### 抢占式多任务处理
在这个模型中，我们让操作系统决定如何通过一个叫做时间片切分的过程在正在执行的工作之间切换。当操作系统在工作之间切换时，我们称之为抢占。

#### 协作式多任务处理
在这种模型中，我们不再依赖操作系统来决定何时在正在执行的工作之间切换，而是明确地在我们的应用程序中编写了代码点，以便我们可以让其他任务运行。

### 1.3.5 合作多任务的好处
asyncio 使用协作多任务来达到并发。当我们的应用程序到达一个可以等待结果返回的点时，我们在代码中明确标记这一点。这允许我们在后台等待结果返回的同时运行其他代码。一旦我们标记的任务完成，我们实际上从等待状态激活并恢复执行任务。

与抢占式多任务相比，协作式多任务具有优势。首先，协作式多任务消耗的资源更少。第二个好处是粒度，在协作多任务中，我们明确标记了最适合暂停任务的时间段。现在，我们了解了并发性、并行性和多任务，我们将使用这些概念来了解如何在 Python 中使用线程和进程实现它们。

### 1.4 理解进程、线程、多线程和多处理
让我们先从进程和线程的定义开始。

### 1.4.1 进程
进程是运行的应用程序，具有其他应用程序无法访问的内存空间。创建 Python 进程的一个例子是运行一个简单的 “hello world” 应用程序或通过在命令行中键入 python 来启动 REPL（读取、求值、打印循环）。

多个进程可以在同一台机器上运行。如果我们的机器有一个具有多个核心的 CPU，我们就可以同时执行多个进程。如果我们的机器只有一个核心的 CPU，我们仍然可以通过分时处理同时运行多个应用程序。当操作系统使用分时处理时，它会在一定时间后自动切换正在运行的进程。

### 1.4.2 线程
线程可以被视为重量较轻的进程。此外，它们是操作系统可以管理的最小管理块。与进程不同，它们没有自己的内存；相反，它们与创建它们的进程共享内存。线程与创建它们的进程相关联。一个进程将始终与至少一个线程相关联，通常称为主线程。进程还可以创建其他线程，这些线程更常见地被称为工作线程或后台线程。这些线程可以与主线程并发地执行其他工作。线程与进程非常相似，可以在多核 CPU 上并行运行，操作系统还可以通过分时切换它们。当我们运行一个正常的 Python 应用程序时，我们创建了一个进程和一个主线程，它将负责运行我们的 Python 应用程序。

#### Listing1.2 一个简单的 Python 应用程序中的进程和线程
```python
import os
import threading

print(f'Python process running with process id: {os.getpid()}')
total_threads = threading.active_count()
thread_name = threading.current_thread().name 

print(f'Python is currently running {total_threads} thread(s)')
print(f'The current thread is {thread_name}')
```
一个主线程从内存中读取数据的过程。我们创建了一个简单的应用程序，以显示主线程的基本知识。我们首先获取进程 ID（次运行此代码时进程 ID 都会不同）并将其打印出来，以证明我们确实有一个专用进程在运行。然后，我们获取正在运行的线程的活动计数以及当前线程的名称，以显示我们正在运行一个主线程。

#### Listing1.3 创建多线程 Python 应用程序
```python
import threading

def hello_from_thread():
    print(f'Hello from Thread {threading.current_thread()}!')

hello_thread = threading.Thread(target=hello_from_thread)
hello_thread.start()

total_threads = threading.active_count()
thread_name = threading.current_thread().name

print(f'Python is currently running {total_threads} thread(s)')
print(f'The current thread is {thread_name}')

hello_thread.join()
```
一个具有两个工作线程和一个主线程的多线程程序，每个线程都共享进程的内存。我们创建了一个方法来打印出当前线程的名称，然后创建一个线程来运行该方法。然后，我们调用线程的 start 方法来开始运行它。最后，我们调用 join 方法。join 将导致程序暂停，直到我们启动的线程完成。

在许多编程语言中，多线程应用程序是实现并发的一种常见方式。然而，在 Python 中使用线程进行并发存在一些挑战。多线程仅适用于 I/O 受限的工作，因为我们受到全局解释器锁的限制。多线程不是我们实现并发的唯一方式；我们还可以创建多个进程同时为我们工作。这被称为多进程。在多进程中，父进程创建一个或多个子进程，由它管理。然后它可以将工作分配给子进程。

Python 为我们提供了 multiprocessing 模块来处理这个问题。其 API 与 threading 模块的 API 类似。我们首先创建一个带有目标函数的进程，然后调用其 start 方法来执行它，最后调用其 join 方法来等待它完成运行。

#### Listing1.4 创建多个进程
```python
import multiprocessing
import os

def hello_from_process():
    print(f'Hello from child process {os.getpid()}!')

if __name__ == '__main__':
    hello_process = multiprocessing.Process(target=hello_from_process)
    hello_process.start()
    print(f'Hello from parent process {os.getpid()}')
    hello_process.join()
```
使用一个父进程和两个子进程进行多处理的应用程序。我们创建了一个子进程，该子进程打印其进程 ID，我们还打印出父进程 ID，以证明我们正在运行不同的进程。当我们有 CPU 密集型工作时，多进程通常是最好的。

### 1.5 理解 GIL
全局解释器锁是 Python 社区中的一个有争议的话题。简而言之，GIL 会在任何时候阻止一个 Python 进程执行超过一个 Python 字节码指令。这意味着即使我们在具有多个核的机器上具有多个线程，一个 Python 进程一次也只能运行一个线程的 Python 代码。注意多处理可以同时运行多个字节码指令，因为每个 Python 进程都有自己的 GIL。

那么为什么存在 GIL 呢？答案在于 CPython 中的内存管理方式。在 CPython 中，内存主要由一个称为引用计数的过程进行管理。引用计数通过跟踪当前需要访问特定 Python 对象（例如整数、字典或列表）的人来工作。引用计数是一个整数，用于跟踪有多少地方引用了特定对象。当某人不再需要引用的对象时，引用计数会递减，当其他人需要它时，它会递增。当引用计数达到零时，没有人引用该对象，它可以从内存中删除。

#### 什么是 CPython
线程冲突的产生在于 CPython 的实现并非线程安全的。当我们说 CPython 不是线程安全时，意思是如果两个或多个线程修改一个共享变量，该变量可能会最终处于意外的状态。这种意外状态取决于线程访问该变量的顺序，通常称为竞态条件。当两个线程需要同时引用一个 Python 对象时，就可能出现竞态条件。

为了展示 GIL 对多线程编程的影响，让我们来看看计算斐波那契数列中第 n 个数字的 CPU 密集型任务。我们将使用一个相当慢的算法实现来演示一个时间密集型操作。一个适当的解决方案将利用 memoization 或数学技术来提高性能。

#### Listing1.5 生成斐波那契数列并计时
```python
import time

def print_fib(number: int) -> None:
    def fib(n: int) -> int:
        if n == 1:
            return 0
        elif n == 2:
            return 1
        else:
            return fib(n - 1) + fib(n - 2)
    
    print(f'fib({number}) is {fib(number)}')

def fibs_no_threading():
    print_fib(40)
    print_fib(41)

start = time.time()
fibs_no_threading()
end = time.time()

print(f'Completed in {end - start:.4f} seconds.')
```
这个实现使用了递归，总体上是一个相对较慢的算法，需要指数级的时间来完成。如果我们需要打印两个斐波那契数，同步调用它们并计时结果很容易，就像我们在前面的列表中做的那样。

#### Listing1.6 斐波那契数列的多线程
```python
import threading
import time

def print_fib(number: int) -> None:
    def fib(n: int) -> int:
        if n == 1:
            return 0
        elif n == 2:
            return 1
        else:
            return fib(n - 1) + fib(n - 2)

def fibs_with_threads():
    thread_40 = threading.Thread(target=print_fib, args=(40,))
    thread_41 = threading.Thread(target=print_fib, args=(41,))

    thread_40.start()
    thread_41.start()

    thread_40.join()
    thread_41.join()

start_threads = time.time()
fibs_with_threads()
end_threads = time.time()

print(f'Threads took {end_threads - start_threads:.4f} seconds.')
```
我们的多线程版本花费了几乎相同的时间。事实上，它甚至有点慢！这几乎完全归因于 GIL 和创建和管理线程的开销。虽然线程确实是并发运行的，但由于锁定，只有一个线程可以一次运行 Python 代码。这使其他线程处于等待状态，直到第一个线程完成，这完全否定了多线程的价值。