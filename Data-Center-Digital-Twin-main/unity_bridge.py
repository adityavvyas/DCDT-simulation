import asyncio
import websockets
import threading
import json

class UnityBridge:
    def __init__(self, port=8765):
        self.port = port
        self.loop = asyncio.new_event_loop()
        self.clients = set()
        self.thread = threading.Thread(target=self._run_loop, daemon=True)
        self.thread.start()
        print(f"Unity Bridge started on port {port}")

    def _run_loop(self):
        asyncio.set_event_loop(self.loop)
        
        async def start_server():
            # Use async context manager for the server
            async with websockets.serve(self._handler, "localhost", self.port):
                await asyncio.Future() # Run forever

        try:
            self.loop.run_until_complete(start_server())
        except Exception as e:
            print(f"Unity Bridge Error: {e}")

    async def _handler(self, websocket, *args):
        # Accepts *args to handle both (ws) and (ws, path) signatures
        print("Unity Client Connected")
        self.clients.add(websocket)
        try:
            await websocket.wait_closed()
        except:
            pass
        finally:
            self.clients.remove(websocket)
            print("Unity Client Disconnected")

    def send_update(self, data):
        """
        Thread-safe method to send data to all connected clients.
        """
        if not self.clients:
            return
        
        json_data = json.dumps(data)
        # Schedule the send in the event loop
        asyncio.run_coroutine_threadsafe(self._broadcast(json_data), self.loop)

    async def _broadcast(self, message):
        if self.clients:
            # Send to all clients, ignoring errors from disconnected ones
            await asyncio.gather(*[client.send(message) for client in self.clients], return_exceptions=True)
