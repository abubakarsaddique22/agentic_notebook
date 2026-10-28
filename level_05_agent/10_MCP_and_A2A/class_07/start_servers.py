
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
        # 3. Start all servers
        for name in SERVERS:

            path = ROOT / "servers" / name

            process = subprocess.Popen(
                [sys.executable, str(path)],
                cwd=ROOT
            )

            processes.append(process)

            print(f"Started: {name} | PID: {process.pid}")

        print("\nAll MCP servers launched!")
        print("Run python agent.py in another terminal.")

        # 4. Monitor servers
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
        # 5. Stop all servers
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
