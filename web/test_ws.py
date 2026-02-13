import asyncio
import websockets

async def test_connection():
    uri = "ws://127.0.0.1:8000/ws/post/1/comments/" 
    try:
        async with websockets.connect(uri) as websocket:
            print(f"Successfully connected to {uri}")
            await websocket.close()
    except Exception as e:
        print(f"Failed to connect to {uri}: {e}")

if __name__ == "__main__":
    asyncio.run(test_connection())
