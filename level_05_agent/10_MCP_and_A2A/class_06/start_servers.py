
import subprocess
import sys
import time
from pathlib import Path

# 1. Project folder
ROOT = Path(__file__).resolve().parent

# 2. MCP Server files
SERVERS = [
    "travel_server.py",
    "policy_server.py",
    "work_server.py"
]


def main():

    processes = []

    try:
        # 3. Start all MCP Servers
        for server in SERVERS:

            path = ROOT / "servers" / server

            process = subprocess.Popen(
                [sys.executable, str(path)]
            )

            processes.append(process)

            print(f"Started: {server}")

        print("\nAll MCP servers launched!")
        print("Open another terminal and run: python agent.py")

        # 4. Keep checking servers
        while True:

            for process in processes:
                if process.poll() is not None:
                    raise RuntimeError(
                        f"Server stopped with code {process.returncode}"
                    )

            time.sleep(1)

    except KeyboardInterrupt:
        print("\nStopping MCP Servers...")

    finally:
        # 5. Stop all MCP Servers
        for process in processes:
            if process.poll() is None:
                process.terminate()

        for process in processes:
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()


if __name__ == "__main__":
    main()
