# 使用 asyncio 的 Python 并发

项目来源：[链接](https://www.manning.com/books/python-concurrency-with-asyncio)

## 第三章：第一个异步IO应用程序

### 本章涵盖

1. 使用套接字在网络上传输数据。
2. 使用 telnet 与基于套接字的应用程序进行通信。
3. 使用选择器为非阻塞套接字构建简单的事件循环。
4. 创建一个允许多个连接的非阻塞回显服务器。
5. 处理任务中的异常。
6. 为 asyncio 应用程序添加自定义关闭逻辑。

在前两章中，我们介绍了协程、任务和事件循环。我们还学习了如何并行执行耗时较长的操作，并探讨了 asyncio 中一些用于实现这一目标的相关 API。不过到目前为止，我们使用的都是 sleep 函数来模拟耗时较长的操作。

由于我们希望构建的不仅仅是演示应用程序，因此将使用一些真实的阻塞操作来展示如何创建能够同时处理多个用户的服务器。我们将仅使用一个线程来实现这一目标，这样相比那些需要使用多个线程或进程的解决方案，应用程序在资源利用和实现复杂性方面会更加高效简洁。我们将运用所学到的协程、任务以及 asyncio 的 API 方法，通过套接字构建一个可运行的命令行回显服务器应用程序来加以演示。本章结束时，你将能够使用 asyncio 和套接字构建出能够通过单个线程同时处理多个用户的网络应用程序。

首先，我们将学习如何使用阻塞式套接字发送和接收数据的基本原理。然后，我们将利用这些套接字尝试构建一个多客户端回显服务器。通过这个过程，我们会发现仅使用单个线程无法构建能够同时正确处理多个客户端的回显服务器。接下来，我们将学习如何通过将套接字设置为非阻塞模式并利用操作系统的事件通知机制来解决这些问题。这将有助于我们理解 asyncio 事件循环的底层工作原理。之后，我们将使用 asyncio 的非阻塞套接字协程来让多个客户端能够正常连接。该应用程序允许多个用户同时连接，并可让他们并发地发送和接收消息。最后，我们还会为应用程序添加自定义的关闭逻辑，这样在服务器关闭时，可以给正在传输中的消息一些时间来完成传输。

### 3.1 使用阻塞套接字

套接字是一种在网络上传输数据的方式。客户端连接到我们的服务器套接字。随后，服务器创建一个新的套接字与客户端进行通信。我们使用 socket 函数来创建一个套接字。

#### 什么是 TCP 协议

调用 socket.socket 可以创建一个套接字，但我们还不能开始与之通信，因为该套接字尚未绑定到客户端可以连接的地址上（就像邮局需要有一个地址一样）。在这个例子中，我们将把套接字绑定到本地计算机的地址 127.0.0.1 上，并选择任意端口号 8000。

接下来，我们需要主动监听来自希望连接我们服务器的客户的连接请求。为此，可以调用套接字的“监听”方法。该方法会让套接字开始等待外部连接，这样客户就能连接到我们的服务器套接字上了。之后，通过调用套接字的“接受”方法来等待连接建立。此方法会一直阻塞，直到有连接进来为止；连接建立后，它会返回一个连接对象以及连接客户的地址信息。这个连接其实也是一个套接字，我们可以利用它向客户端发送数据或从客户端接收数据。

有了这些组件，我们就具备了创建基于套接字的服务器应用程序所需的所有条件：该程序能够等待连接建立，并在连接到来时打印一条消息。

#### Listing3.1 启动服务器并监听连接

```python
import socket

server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.setsockopt(socket.SOCKET, socket.SO_REUSEADDR, 1)
server_address = ('127.0.0.1', 8000)
server_socket.bind(server_address)
server_socket.listen()

connection, client_address = server_socket.accept()
print(f'I got a connection from {client_address}!')
```

既然我们已经开发好了这个应用程序，那么要如何连接它来进行测试呢？虽然有不少工具可以做到这一点，但在本章中我们将使用telnet命令行工具。

### 3.2 使用 telnet 连接服务器

要连接到我们在上一个小节中构建的服务器，可以在命令行中使用telnet命令，并指定要连接至本地主机上的8000端口。在服务器应用程序的控制台输出中，我们现在应该能看到如下所示的输出，表明我们已经通过telnet客户端建立了连接。

### 3.2.1 通过套接字读取数据

既然我们已经创建了一个能够接受连接的服务器，接下来就了解一下如何从连接中读取数据。Socket类有一个名为recv的方法，可用于从特定套接字中获取数据。该方法接收一个整数参数，表示每次要读取的字节数。这一点很重要，因为我们无法一次性将所有数据从套接字中读出，而需要分批读取直至到达数据末尾。

#### Listing3.2 从套接字中读取数据

```python
import socket

server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

server_address = ('127.0.0.1', 8000)
server_socket.bind(server_address)
server_socket.listen()

try:
    connection, client_address = server_socket.accept()
    print(f'I got a connection from {client_address}!')

    buffer = b''

    while buffer[-2:] != b'\r\n':
        data = connection.recv(2)
        if not data:
            break
        else:
            print(f'I got data: {data}!')
            buffer = buffer + data

    print(f"All the data is: {buffer}")
finally:
    server_socket.close()
```

在前面的代码示例中，我们像之前一样使用 server_socket.accept() 来等待连接。一旦有连接建立，我们就尝试读取两个字节并将其存储在缓冲区中。接着进入循环，每次循环都会检查缓冲区的末尾是否为“回车换行符”\r\n。如果不是，我们就再读取两个字节，并将它们打印出来同时追加到缓冲区中。如果检测到\r\n字符，循环结束，我们将从客户端接收到的完整消息打印出来。最后，我们在finally块中关闭服务器socket，这样可以确保在读取数据时出现异常也能成功断开连接。如果我们使用telnet连接到该应用程序并发送消息“testing123”，将会看到如下输出。

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