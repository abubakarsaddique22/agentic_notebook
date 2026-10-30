"""Internal MCP protocol availability exporter. Expose only to internal Docker network."""
import asyncio
import logging
import os
import time
from mcp import Client
from prometheus_client import Gauge, Counter, start_http_server
from json_logging import setup_logging

URLS = {'travel': os.getenv('TRAVEL_MCP_URL', 'http://travel:8001/mcp'),
        'policy': os.getenv('POLICY_MCP_URL', 'http://policy:8002/mcp'),
        'work': os.getenv('WORK_MCP_URL', 'http://work:8003/mcp')}
UP = Gauge('mcp_protocol_up', 'Successful MCP initialization and list_tools', ['service'])
LATENCY = Gauge('mcp_probe_duration_seconds', 'MCP probe duration', ['service'])
FAILURES = Counter('mcp_probe_failures_total', 'Failed MCP probes', ['service'])

async def probe(service, url):
    started = time.monotonic()
    try:
        async with asyncio.timeout(12):
            async with Client(url) as client:
                assert (await client.list_tools()).tools
        UP.labels(service).set(1)
        logging.info('probe_ok service=%s', service)
    except Exception as exc:
        UP.labels(service).set(0)
        FAILURES.labels(service).inc()
        logging.warning('probe_failed service=%s reason=%s', service, type(exc).__name__)
    finally:
        LATENCY.labels(service).set(time.monotonic() - started)

async def main():
    setup_logging()
    start_http_server(9100, addr='0.0.0.0')
    while True:
        await asyncio.gather(*(probe(name, url) for name, url in URLS.items()))
        await asyncio.sleep(30)

if __name__ == '__main__':
    asyncio.run(main())
