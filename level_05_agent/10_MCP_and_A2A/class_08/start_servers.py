import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SERVERS = ['travel_server.py', 'policy_server.py', 'work_server.py']


def main():
    children = []
    try:
        for name in SERVERS:
            script = ROOT / 'servers' / name
            child = subprocess.Popen([sys.executable, str(script)], cwd=ROOT)
            children.append(child)
            print('Started:', name, '(PID:', child.pid, ')', flush=True)
        print('Use another terminal to run: python test_connections.py or python agent.py')
        while True:
            for child in children:
                if child.poll() is not None:
                    raise RuntimeError(f'Server PID {child.pid} exited with code {child.returncode}')
            import time
            time.sleep(1)
    except KeyboardInterrupt:
        print('\nStopping servers...')
    finally:
        for child in children:
            if child.poll() is None:
                child.terminate()
        for child in children:
            try:
                child.wait(timeout=5)
            except subprocess.TimeoutExpired:
                child.kill()
                child.wait()

if __name__ == '__main__':
    main()
