# 使用 asyncio 的 Python 并发
https://www.manning.com/books/python-concurrency-with-asyncio

## 第一章 了解 asyncio

### 本章涵盖
1. Asyncio 是什么？以及它提供的好处。
2. 并发性、并行性、线程和进程。
3. 全局解释器锁及其对并发性的挑战。
4. 非阻塞套接字如何仅使用一个线程实现并发。
5. 基于事件循环并发的基本原理。

Web 应用依赖于输入输出（I/O）操作，同时发出许多 I/O 请求可能会导致严重的性能问题。asyncio 最初在 Python 3.4 中引入，是除了多线程和多进程之外处理这些高度并发工作负载的另一种方式。正确地使用这个库可以大幅提高使用 I/O 操作的应用程序的性能和资源利用率，因为它允许我们同时启动许多这些长期运行的任务。

### 1.1 什么是异步
在同步应用中，代码是顺序执行的。并发意味着允许同时处理多个任务。

那么什么是异步编程呢？它意味着一个特定的长期运行任务可以在后台运行，与主应用程序分开。而不是阻塞所有其他应用程序代码等待该长期运行任务完成，系统可以自由地执行不依赖于该任务的其他工作。然后，一旦长期运行任务完成，我们将收到通知，表示任务已完成，这样我们就可以处理结果。

### 1.2 什么是 I/O 绑定和 CPU 绑定
当我们说一个操作是 I/O 限制或 CPU 限制时，我们指的是阻止该操作运行更快的限制因素。这意味着如果我们提高了操作所依赖的限制因素的性能，该操作将在更短的时间内完成。

#### Listing1.1 I/O 绑定和 CPU 绑定操作
```python
import requests

response = requests.get('https://www.example.com')
items = response.headers.items()

headers = [f'{key}:{header}' for key, header in items]
formatted_headers = '\n'.join(headers)         

with open('headers.text', 'w') as file: file.write(formatted_headers)
```
I/O 绑定操作和 CPU 绑定操作通常会并排执行。我们首先发出一个 I/O 绑定请求来下载 https://www.example.com 的内容。一旦收到响应，我们就会执行一个 CPU 绑定循环来格式化响应的标头并将其转换为以换行符分隔的字符串。然后我们打开一个文件并将该字符串写入该文件，这两个操作都是 I/O 绑定操作。

### 1.3 什么是 I/O 绑定和 CPU 绑定
more 