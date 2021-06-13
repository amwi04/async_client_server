import asyncio


async def f():
    r,w = await asyncio.open_connection('localhost',8000)
    w.write(str.encode('hello=>yo'))
    await w.drain()
    data = await r.read(255)
    print(data)
    w.close()
    return data.decode('utf8')

if __name__ == "__main__":
    asyncio.run(f())