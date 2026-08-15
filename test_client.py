import asyncio
import websockets
import json

async def test_client():
    url = "ws://127.0.0.1:8000/ws"
    print(f"Connecting to OmniAI WebSocket at {url}...")
    try:
        async with websockets.connect(url) as websocket:
            print("Connected successfully! Type your command below (or 'exit' to quit).")
            print("Examples:")
            print(" - go to www.google.com")
            print(" - take screenshot")
            print(" - hello (unrecognized command)")
            print("-" * 50)
            
            while True:
                command = input("Enter command: ")
                if command.lower() == 'exit':
                    break
                if not command.strip():
                    continue
                
                # Send command
                await websocket.send(command)
                
                # Receive and parse response
                response = await websocket.recv()
                try:
                    response_json = json.loads(response)
                    print(f"\nServer Response:")
                    print(json.dumps(response_json, indent=2))
                except json.JSONDecodeError:
                    print(f"\nRaw Server Response: {response}")
                print("-" * 50)
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    try:
        asyncio.run(test_client())
    except KeyboardInterrupt:
        print("\nExiting...")
