#!/usr/bin/env python3
"""
Ninode Service Agent - Single File Distribution
Production-ready FastAPI service for VPS management and monitoring
"""

import json
import os
import platform
import shutil
import socket
import subprocess
import sys
import asyncio
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Dict, Any, List, Optional

import httpx
import uvicorn
from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field


# Configuration
class Config(BaseModel):
    api_key: str = Field(..., description="Authentication token for Ninode app")
    server_url: str = Field(..., description="URL of Ninode application")
    port: int = Field(default=6969, description="Service port")
    host: str = Field(default="0.0.0.0", description="Bind address")
    update_interval_hours: int = Field(
        default=24, description="Hours between auto-update checks"
    )
    enable_auto_update: bool = Field(
        default=True, description="Enable automatic updates"
    )


def load_config(config_path: Optional[str] = None) -> Config:
    if config_path is None:
        config_path = "/opt/ninode/config.json"

    config_file = Path(config_path)

    if not config_file.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")

    try:
        with open(config_file, "r") as f:
            config_data = json.load(f)

        return Config(**config_data)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in configuration file: {e}")
    except Exception as e:
        raise RuntimeError(f"Failed to load configuration: {e}")


# Registration
async def get_system_info() -> Dict[str, Any]:
    hostname = socket.gethostname()

    try:
        local_ip = socket.gethostbyname(hostname)
    except socket.gaierror:
        local_ip = "127.0.0.1"

    return {
        "status": "online",
        "version": CURRENT_VERSION,
        "hostname": hostname,
        "platform": {
            "system": platform.system(),
            "release": platform.release(),
            "version": platform.version(),
            "machine": platform.machine(),
            "processor": platform.processor(),
        },
        "ip_address": local_ip,
    }


async def register_with_server(config: Config) -> bool:
    system_info = await get_system_info()

    headers = {
        "Authorization": f"Bearer {config.api_key}",
        "Content-Type": "application/json",
    }

    registration_url = f"{config.server_url.rstrip('/')}/api/v1/service/register"

    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.post(
                registration_url,
                headers=headers,
                json=system_info,
            )

            if response.status_code == 200:
                return True
            else:
                print(
                    f"Registration failed with status {response.status_code}: {response.text}"
                )
                return False

        except httpx.TimeoutException:
            print("Registration timed out")
            return False
        except httpx.RequestError as e:
            print(f"Registration request failed: {e}")
            return False
        except Exception as e:
            print(f"Unexpected error during registration: {e}")
            return False


# Auto-update functionality
CURRENT_VERSION = "0.1.2"
UPDATE_CHECK_INTERVAL = 24 * 3600  # 24 hours in seconds


async def check_for_updates() -> Optional[str]:
    """Check GitHub for latest release version"""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                "https://api.github.com/repos/michaelsieminski/ninode-service/releases/latest"
            )
            if response.status_code == 200:
                release_data = response.json()
                latest_version = release_data["tag_name"].lstrip("v")
                if latest_version != CURRENT_VERSION:
                    return latest_version
    except Exception as e:
        print(f"Failed to check for updates: {e}")
    return None


async def download_and_replace_script(version: str) -> bool:
    """Download new version and replace current script"""
    try:
        script_path = os.path.abspath(__file__)
        backup_path = f"{script_path}.backup"

        # Download new version
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"https://raw.githubusercontent.com/michaelsieminski/ninode-service/v{version}/ninode-service.py"
            )
            if response.status_code == 200:
                # Create backup
                shutil.copy2(script_path, backup_path)

                # Write new version
                with open(script_path, "w") as f:
                    f.write(response.text)

                # Make executable
                os.chmod(script_path, 0o755)

                print(f"Updated to version {version}. Restarting...")

                # Schedule restart after response is sent
                asyncio.create_task(restart_service_delayed())
                return True
    except Exception as e:
        print(f"Update failed: {e}")
        # Restore backup if it exists
        backup_path = f"{os.path.abspath(__file__)}.backup"
        if os.path.exists(backup_path):
            shutil.copy2(backup_path, os.path.abspath(__file__))
    return False


async def restart_service_delayed():
    """Restart the service after a short delay to allow response to be sent"""
    await asyncio.sleep(2)  # Wait 2 seconds
    try:
        subprocess.run(["systemctl", "restart", "ninode"], check=False)
    except Exception as e:
        print(f"Failed to restart service: {e}")


async def auto_update_task(config: Config):
    """Background task to check for updates periodically"""
    if not config.enable_auto_update:
        print("Auto-update disabled in configuration")
        return

    interval_seconds = config.update_interval_hours * 3600
    print(f"Auto-update enabled: checking every {config.update_interval_hours} hours")

    while True:
        try:
            await asyncio.sleep(interval_seconds)
            latest_version = await check_for_updates()
            if latest_version:
                print(f"New version {latest_version} available. Updating...")
                await download_and_replace_script(latest_version)
        except Exception as e:
            print(f"Auto-update task error: {e}")


# FastAPI Models
class CommandRequest(BaseModel):
    command: str
    args: List[str] = []


class CommandResponse(BaseModel):
    command: str
    exit_code: int
    stdout: str
    stderr: str


# Security
security = HTTPBearer()

ALLOWED_COMMANDS = {
    "ps",
    "df",
    "free",
    "uptime",
    "whoami",
    "uname",
    "hostname",
    "date",
    "id",
    "w",
    "who",
    "last",
    "lscpu",
    "lsblk",
    "mount",
}


def create_app(config: Config) -> FastAPI:
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        # Startup
        print("Starting Ninode Service Agent...")
        success = await register_with_server(config)
        if success:
            print("Successfully registered with Ninode application")
        else:
            print("Failed to register with Ninode application")

        # Start auto-update task
        update_task = asyncio.create_task(auto_update_task(config))

        yield

        # Shutdown - cancel auto-update task
        update_task.cancel()
        try:
            await update_task
        except asyncio.CancelledError:
            pass

    app = FastAPI(
        title="Ninode Service Agent",
        description="FastAPI service for VPS management and monitoring",
        version=CURRENT_VERSION,
        lifespan=lifespan,
    )

    async def verify_token(
        credentials: HTTPAuthorizationCredentials = Depends(security),
    ):
        if credentials.credentials != config.api_key:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication token",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return credentials.credentials

    @app.get("/health")
    async def health_check():
        return {"status": "healthy", "service": "ninode-agent"}

    @app.get("/status")
    async def get_status(token: str = Depends(verify_token)):
        return await get_system_info()

    @app.get("/metrics")
    async def get_metrics(token: str = Depends(verify_token)):
        try:
            metrics = {}

            if shutil.which("free"):
                result = subprocess.run(
                    ["free", "-m"], capture_output=True, text=True, timeout=5
                )
                if result.returncode == 0:
                    metrics["memory"] = result.stdout

            if shutil.which("df"):
                result = subprocess.run(
                    ["df", "-h"], capture_output=True, text=True, timeout=5
                )
                if result.returncode == 0:
                    metrics["disk"] = result.stdout

            if shutil.which("uptime"):
                result = subprocess.run(
                    ["uptime"], capture_output=True, text=True, timeout=5
                )
                if result.returncode == 0:
                    metrics["uptime"] = result.stdout.strip()

            if platform.system() == "Linux":
                try:
                    with open("/proc/loadavg", "r") as f:
                        metrics["load_average"] = f.read().strip()
                except FileNotFoundError:
                    pass

            return {"metrics": metrics}

        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to collect metrics: {str(e)}",
            )

    @app.post("/execute", response_model=CommandResponse)
    async def execute_command(
        request: CommandRequest, token: str = Depends(verify_token)
    ):
        command = request.command.strip()

        if command not in ALLOWED_COMMANDS:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Command '{command}' is not allowed. Allowed commands: {sorted(ALLOWED_COMMANDS)}",
            )

        if not shutil.which(command):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Command '{command}' not found on system",
            )

        try:
            cmd_args = [command] + request.args

            result = subprocess.run(
                cmd_args, capture_output=True, text=True, timeout=30, check=False
            )

            return CommandResponse(
                command=" ".join(cmd_args),
                exit_code=result.returncode,
                stdout=result.stdout,
                stderr=result.stderr,
            )

        except subprocess.TimeoutExpired:
            raise HTTPException(
                status_code=status.HTTP_408_REQUEST_TIMEOUT,
                detail="Command execution timed out",
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Command execution failed: {str(e)}",
            )

    @app.post("/update")
    async def trigger_update(token: str = Depends(verify_token)):
        """Manually trigger update check and download if available"""
        try:
            latest_version = await check_for_updates()
            if latest_version:
                print(f"Manual update triggered: {CURRENT_VERSION} -> {latest_version}")
                success = await download_and_replace_script(latest_version)
                if success:
                    return {
                        "status": "updating",
                        "from_version": CURRENT_VERSION,
                        "to_version": latest_version,
                    }
                else:
                    raise HTTPException(
                        status_code=500, detail="Update download failed"
                    )
            else:
                return {"status": "up_to_date", "current_version": CURRENT_VERSION}
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Update failed: {str(e)}")

    return app


def main():
    try:
        config = load_config()
    except Exception as e:
        print(f"Error loading configuration: {e}")
        sys.exit(1)

    app = create_app(config)

    print(f"Starting Ninode Service Agent on {config.host}:{config.port}")

    uvicorn.run(
        app, host=config.host, port=config.port, access_log=True, log_level="info"
    )


if __name__ == "__main__":
    main()
