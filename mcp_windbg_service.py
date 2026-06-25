"""
Windows service wrapper for:
    python -m mcp_windbg --transport streamable-http --host 0.0.0.0 --port 1203
"""
import importlib
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

try:
    servicemanager = importlib.import_module("servicemanager")
    win32event = importlib.import_module("win32event")
    win32service = importlib.import_module("win32service")
    win32serviceutil = importlib.import_module("win32serviceutil")
except ImportError as exc:
    raise SystemExit("pywin32 is required. Run: python -m pip install pywin32") from exc

ServiceFramework = win32serviceutil.ServiceFramework

SERVICE_NAME = "MCPWinDbg"
HOST = "0.0.0.0"
PORT = "1203"
INSTALL_DIR = Path(os.environ.get("ProgramData", r"C:\ProgramData")) / "mcp_windbg_service"
LOG_DIR = INSTALL_DIR / "logs"


def get_python_executable() -> str:
    current = Path(sys.executable)
    if current.name.lower() == "pythonservice.exe":
        python_exe = current.with_name("python.exe")
        if python_exe.exists():
            return str(python_exe)
    return sys.executable


class MCPWinDbgService(ServiceFramework):
    _svc_name_: str = SERVICE_NAME
    _svc_display_name_: str = "MCP WinDbg HTTP Service"
    _svc_description_: str = "Runs mcp_windbg streamable-http server."

    def __init__(self, args: list[str]):
        super().__init__(args)
        self.stop_event = win32event.CreateEvent(None, 0, 0, None)
        self.process = None
        self.stdout_handle = None
        self.stderr_handle = None

    def SvcStop(self):
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        win32event.SetEvent(self.stop_event)
        self.stop_child_process()

    def SvcDoRun(self):
        servicemanager.LogMsg(
            servicemanager.EVENTLOG_INFORMATION_TYPE,
            servicemanager.PYS_SERVICE_STARTED,
            (self._svc_name_, ""),
        )
        self.run_service_loop()

    def run_service_loop(self):
        while True:
            if win32event.WaitForSingleObject(self.stop_event, 1000) == win32event.WAIT_OBJECT_0:
                break

            if self.process is None or self.process.poll() is not None:
                if self.process is not None:
                    self.log_event(f"mcp_windbg exited with code {self.process.returncode}, restarting")
                    self.close_log_handles()
                    if win32event.WaitForSingleObject(self.stop_event, 5000) == win32event.WAIT_OBJECT_0:
                        break
                self.start_child_process()

        self.stop_child_process()
        self.close_log_handles()

    def start_child_process(self):
        INSTALL_DIR.mkdir(parents=True, exist_ok=True)
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        command = [
            get_python_executable(),
            "-m",
            "mcp_windbg",
            "--transport",
            "streamable-http",
            "--host",
            HOST,
            "--port",
            PORT,
        ]

        self.stdout_handle = open(LOG_DIR / "stdout.log", "a", encoding="utf-8", errors="replace")
        self.stderr_handle = open(LOG_DIR / "stderr.log", "a", encoding="utf-8", errors="replace")

        started_at = datetime.now().isoformat(timespec="seconds")
        command_text = subprocess.list2cmdline(command)
        self.stdout_handle.write(f"\n[{started_at}] starting: {command_text}\n")
        self.stdout_handle.flush()
        self.log_event(f"starting: {command_text}")

        creationflags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
        self.process = subprocess.Popen(
            command,
            cwd=str(INSTALL_DIR),
            env=os.environ.copy(),
            stdin=subprocess.DEVNULL,
            stdout=self.stdout_handle,
            stderr=self.stderr_handle,
            creationflags=creationflags,
        )

    def stop_child_process(self):
        if self.process is None or self.process.poll() is not None:
            return
        self.log_event("stopping mcp_windbg")
        self.process.terminate()
        try:
            _ = self.process.wait(timeout=15)
        except subprocess.TimeoutExpired:
            self.log_event("mcp_windbg did not stop in time, killing it")
            self.process.kill()
            _ = self.process.wait(timeout=10)

    def close_log_handles(self):
        for handle in (self.stdout_handle, self.stderr_handle):
            if handle:
                try:
                    handle.flush()
                    handle.close()
                except OSError:
                    pass
        self.stdout_handle = None
        self.stderr_handle = None

    def log_event(self, message: str) -> None:
        try:
            servicemanager.LogInfoMsg(f"{SERVICE_NAME}: {message}")
        except Exception:
            pass


if __name__ == "__main__":
    win32serviceutil.HandleCommandLine(MCPWinDbgService)
