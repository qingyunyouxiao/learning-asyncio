# 使用 asyncio 的 Python 并发

https://www.manning.com/books/python-concurrency-with-asyncio

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
    connection.sendall(buffer)
finally:
    server_socket.close()
```

在前面的代码示例中，我们像之前一样使用 server_socket.accept() 来等待连接。一旦有连接建立，我们就尝试读取两个字节并将其存储在缓冲区中。接着进入循环，每次循环都会检查缓冲区的末尾是否为“回车换行符”\r\n。如果不是，我们就再读取两个字节，并将它们打印出来同时追加到缓冲区中。如果检测到\r\n字符，循环结束，我们将从客户端接收到的完整消息打印出来。最后，我们在finally块中关闭服务器socket，这样可以确保在读取数据时出现异常也能成功断开连接。当缓存区满后，调用connection.sendall将其中的消息回传给客户端。

### 3.2.2 允许多个连接和及阻塞带来的风险

处于监听模式的套接字可以同时接受多个客户端的连接。这意味着我们可以反复调用 socket.accept 函数，每当有客户端连接上来时，就能获得一个新的连接套接字，从而与该客户端进行数据的读写操作。掌握了这一原理后，我们就可以轻松地将之前的示例修改为能够处理多个客户端。程序会进入无限循环，不断调用 socket.accept 来监听新的连接。每当有新连接建立时，就会将其添加到已连接的客户端列表中。随后，程序会遍历每个连接，接收传入的数据，并将数据重新发送回客户端。

#### Listing3.3 允许多个客户端连接

```python
import socket

server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

server_address = ('127.0.0.1', 8080)
server_socket.bind(server_address)
server_socket.listen()
connections = []

try:
    while True:
        connection, client_address = server_socket.accept()
        print(f'I got a connection from {client_address}!')
        connections.append(connection)
        for connection in connections:
            buffer = b''

            while buffer[-2:] != b'\r\n':
                data = connection.recv(2)
                if not data:
                    break
                else:
                    print(f'I got data: {data}')
                    buffer += data

            print(f'All the data is: {buffer}')
            connection.send(buffer)
finally:
    server_socket.close()
```

我们可以尝试通过telnet建立第一个连接并输入一条消息。之后，再用第二个telnet客户端连接并发送另一条消息。但这样做时会立即发现问题：第一个客户端能正常工作，并按预期回显消息；而第二个客户端却收不到任何回复。这是因为套接字的默认阻塞机制所致。accept和recv函数在接收到数据前会一直处于阻塞状态。也就是说，当第一个客户端连接后，我们会一直等待它发送第一条回显消息，从而导致其他客户端也无法进入循环的下一轮处理，直到第一个客户端向我们发送数据为止。

在使用阻塞式套接字的情况下，客户端1能够成功连接，而客户端2则会被阻塞，直到客户端1发送数据为止。

### 3.3 使用非阻塞套接字

我们之前的回声服务器允许多个客户端连接；然而，当多个客户端同时连接时，会出现某个客户端导致其他客户端必须等待其发送数据的问题。我们可以通过将套接字设置为非阻塞模式来解决这个问题。这样一来，每当调用可能造成阻塞的方法（如recv）时，该方法都能立即返回结果。如果套接字中有待处理的数据，我们会像使用阻塞套接字时一样收到数据；如果没有数据，套接字会立即告知我们暂无数据可用，这样我们就可以继续执行其他代码了。

#### Listing 3.4 创建非阻塞套接字

```python
import socket

server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

server_address = ('127.0.0.1', 8080)
server_socket.bind(server_address)
server_socket.listen()

server_socket.setblocking(False)
```

从根本上说，创建非阻塞套接字与创建阻塞套接字并无不同，只不过需要将 `setblocking` 设置为 `False`。默认情况下，套接字的此值为 `True`，表示其为阻塞模式。现在让我们在原来的应用程序中尝试这样做，看看是否能够解决问题。

#### Listing 3.5 首次尝试实现非阻塞服务器

```python
import socket

server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

server_address = ('127.0.0.1', 8080)
server_socket.bind(server_address)
server_socket.listen()
server_socket.setblocking(False)

connections = []

try:
    while True:
        connection, client_address = server_socket.accept()
        connection.setblocking(False)
        print(f'I got a connection from {client_address}!')
        connections.append(connection)

        for connection in connections:
            buffer = b''

            while buffer[-2:] != b'\r\n':
                data = connection.recv(2)
                if not data:
                    break
                else:
                    print(f'I got data: {data}!')
                    buffer = buffer + data

            print(f"All the data is: {buffer}")
            connection.send(buffer)
finally:
    server_socket.close()
```

我们无法轻易判断套接字当前是否有数据，因此一种解决办法是捕获异常、忽略它，然后持续循环等待数据的到来。通过这种方式，我们可以尽可能快地检查新的连接和数据。这应该能解决我们之前使用的阻塞式套接字回声服务器所遇到的问题。

#### Listing 3.6 捕获并忽略阻塞式 I/O 错误

```python
import socket

server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server_address = ('127.0.0.1', 8080)
server_socket.bind(server_address)
server_socket.listen()
server_socket.setblocking(False)

connections = []

try:
    while True:
        try:
            connection, client_address = server_socket.accept()
            connection.setblocking(False)
            print(f'I got a connection from {client_address}!')
            connections.append(connection)
        except BlockingIOError:
            pass
    
        for connection in connections:
            try:    
                buffer = b''

                while buffer[-2:] != b'\r\n':
                    data = connection.recv(2)
                    if not data:
                        break
                    else:
                        print(f'I got data: {data}!')
                        buffer = buffer + data

                print(f"All the data is: {buffer}")
                connection.send(buffer)
            except BlockingIOError:
                pass   
finally:
    server_socket.close()
```

在无限循环的每次迭代中，我们调用 accept 或 recv 函数时，要么立即抛出被忽略的异常，要么有可处理的数据可供处理。循环的每次迭代都进行得非常迅速，我们无需等待他人发送数据才能执行下一条代码。这样一来，既解决了阻塞式服务器的问题，又能让多个客户端同时连接并发送数据。

这种方法确实有效，但也有代价。首先是代码质量方面的问题：每当可能还没有数据时就去捕获异常，会导致代码变得冗长且容易出错。其次是资源消耗问题：如果在笔记本电脑上运行该程序，几秒钟后就会发现风扇转速加快。。这是因为程序中不断循环并快速捕获异常，从而产生了高 CPU 负荷的工作负载。