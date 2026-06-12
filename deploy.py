import paramiko
import os
import sys
import time

HOST = "120.79.28.144"
PORT = 22
USER = "root"
KEY_PATH = "C:\\Users\\Admin\\Downloads\\LIU.pem"
REMOTE_DIR = "/root/stock-game"
LOCAL_DIR = "D:\\hl\\炒股"

def should_include(rel_path):
    skip_dirs = {"__pycache__", ".git", "venv", ".venv", "node_modules"}
    skip_ext = {".pyc", ".pyo", ".db"}
    parts = rel_path.split(os.sep)
    for p in parts:
        if p in skip_dirs:
            return False
    ext = os.path.splitext(rel_path)[1].lower()
    if ext in skip_ext:
        return False
    if rel_path == "deploy.py":
        return False
    return True

def main():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    key = paramiko.RSAKey.from_private_key_file(KEY_PATH)

    print(f"Connecting to {HOST} as {USER}...")
    ssh.connect(HOST, PORT, USER, pkey=key, look_for_keys=False, allow_agent=False, timeout=15)
    print("Connected!")

    # Upload files via SFTP
    print(f"\nUploading to {REMOTE_DIR}...")
    sftp = ssh.open_sftp()
    uploaded = 0
    total = 0

    # Count first
    for root, dirs, files in os.walk(LOCAL_DIR):
        for f in files:
            rel_path = os.path.relpath(os.path.join(root, f), LOCAL_DIR)
            if should_include(rel_path):
                total += 1

    # Upload
    for root, dirs, files in os.walk(LOCAL_DIR):
        for f in files:
            local_path = os.path.join(root, f)
            rel_path = os.path.relpath(local_path, LOCAL_DIR)
            if not should_include(rel_path):
                continue
            remote_path = f"{REMOTE_DIR}/{rel_path.replace(os.sep, '/')}"
            remote_dir = os.path.dirname(remote_path)

            try:
                sftp.stat(remote_dir)
            except FileNotFoundError:
                ssh.exec_command(f"mkdir -p {remote_dir}")

            sftp.put(local_path, remote_path)
            uploaded += 1
            pct = uploaded * 100 // total
            bar = "█" * (pct // 5) + "░" * (20 - pct // 5)
            sys.stdout.write(f"\r  [{uploaded}/{total}] {rel_path}  ")
            sys.stdout.flush()

    sftp.close()
    print(f"\nUploaded {uploaded} files.")

    # Restart server
    print("Restarting server...")
    cmds = [
        # Kill existing screen session
        "screen -S stock-game -X quit 2>/dev/null || true",
        "sleep 1",
        f"cd {REMOTE_DIR}",
        # Install deps
        f"{REMOTE_DIR}/venv/bin/pip install -q -r {REMOTE_DIR}/backend/requirements.txt 2>&1 || pip install -q -r {REMOTE_DIR}/backend/requirements.txt",
        # Start new screen session
        f"screen -dmS stock-game bash -c 'cd {REMOTE_DIR} && {REMOTE_DIR}/venv/bin/uvicorn backend.main:app --host 0.0.0.0 --port 8000 2>&1 | tee {REMOTE_DIR}/server.log'",
    ]

    for cmd in cmds:
        _, stdout, stderr = ssh.exec_command(cmd)
        exit_code = stdout.channel.recv_exit_status()
        if exit_code != 0:
            err = stderr.read().decode().strip()
            if err:
                print(f"  cmd exit {exit_code}: {err[:100]}")

    time.sleep(5)

    # Verify
    print("\nVerifying...")
    _, stdout, _ = ssh.exec_command("curl -s http://localhost:8000/api/health")
    result = stdout.read().decode().strip()

    _, stdout, _ = ssh.exec_command(f"tail -10 {REMOTE_DIR}/server.log 2>/dev/null || echo 'no log file'")
    logs = stdout.read().decode().strip()

    print(f"  Health: {result}")
    print(f"  Logs: {logs[-300:]}" if logs.isascii() else "  Logs: (see server.log)")

    ssh.close()

    if '"status":"ok"' in result:
        print("\nDeploy OK! http://120.79.28.144")
    else:
        print(f"\nDeploy WARN: {result}")

if __name__ == "__main__":
    main()
