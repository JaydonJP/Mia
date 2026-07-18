import subprocess

def run_powershell(cmd: str):
    # Simple allowlist for safety
    safe_prefixes = ["dir", "ls", "echo", "Get-Process", "Get-Date", "ping", "ipconfig"]
    is_safe = any(cmd.strip().startswith(prefix) for prefix in safe_prefixes)
    if not is_safe:
        return f"Command '{cmd}' blocked by safety policy. Only safe commands are allowed in auto mode."
        
    try:
        result = subprocess.run(["powershell", "-Command", cmd], capture_output=True, text=True, timeout=10)
        out = result.stdout if result.returncode == 0 else result.stderr
        # Truncate if too long
        if len(out) > 2000:
            out = out[:2000] + "\n...[truncated]"
        return out
    except Exception as e:
        return f"Shell execution failed: {e}"
