"""
Shared test fixtures.

Provides an async-compatible `client` fixture that supports:
- await client.post(...)   — via httpx.AsyncClient + ASGITransport
- async with client.websocket_connect("/ws") as ws   — wraps starlette TestClient
"""
import asyncio
import contextlib
import pytest
import httpx
from starlette.testclient import TestClient
from src.main import app


class _AsyncWebSocketWrapper:
    """Wraps starlette's sync WebSocketTestSession as an async context manager."""

    def __init__(self, session):
        self._session = session

    async def send_text(self, text: str):
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, self._session.send_text, text)

    async def receive_text(self) -> str:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._session.receive_text)

    async def close(self, code: int = 1000):
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, self._session.close, code)


class _AsyncWebSocketContext:
    def __init__(self, sync_ctx):
        self._sync_ctx = sync_ctx

    def __enter__(self):
        raise RuntimeError("Use `async with`, not `with`")

    def __exit__(self, *args):
        pass

    async def __aenter__(self):
        loop = asyncio.get_event_loop()
        session = await loop.run_in_executor(None, self._sync_ctx.__enter__)
        self._session = session
        return _AsyncWebSocketWrapper(session)

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, self._sync_ctx.__exit__, exc_type, exc_val, exc_tb)


class _AsyncTestClient:
    """
    Async wrapper around httpx.AsyncClient + starlette TestClient (for WebSockets).
    """

    def __init__(self):
        transport = httpx.ASGITransport(app=app)  # type: ignore[arg-type]
        self._http = httpx.AsyncClient(
            transport=transport,
            base_url="http://testserver",
        )
        self._sync = TestClient(app)

    async def post(self, url: str, **kwargs):
        return await self._http.post(url, **kwargs)

    async def get(self, url: str, **kwargs):
        return await self._http.get(url, **kwargs)

    def websocket_connect(self, url: str, **kwargs):
        return _AsyncWebSocketContext(self._sync.websocket_connect(url, **kwargs))

    async def aclose(self):
        await self._http.aclose()


@pytest.fixture
async def client():
    c = _AsyncTestClient()
    yield c
    await c.aclose()
