"""
Debug and monitoring routes for Phone Recording System.

Provides comprehensive debugging information, performance metrics,
and system monitoring capabilities for troubleshooting and optimization.
"""

import asyncio
import json
import logging
import os
import psutil
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any

from fastapi import APIRouter, Request, HTTPException, Depends
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

from ..core.logging_setup import get_logger
from .websocket_routes import connection_manager

logger = get_logger(__name__)

# Debug router
debug_router = APIRouter(prefix="/debug")

# Get templates directory
current_dir = Path(__file__).parent
templates = Jinja2Templates(directory=str(current_dir / "templates"))


class SystemMetrics(BaseModel):
    """System performance metrics."""
    cpu_percent: float
    memory_percent: float
    memory_available_mb: float
    disk_free_gb: float
    uptime_seconds: float
    python_version: str
    process_count: int


class AudioSystemStatus(BaseModel):
    """Audio system status information."""
    blackhole_available: bool
    input_devices_count: int
    output_devices_count: int
    default_input: Optional[str] = None
    default_output: Optional[str] = None
    sample_rates_supported: List[int] = []


class RecordingSystemStatus(BaseModel):
    """Recording system status."""
    active_sessions: int
    total_sessions: int
    recording_in_progress: bool
    last_recording_time: Optional[str] = None
    total_recording_duration: float = 0.0
    recordings_today: int = 0


class WebSocketStatus(BaseModel):
    """WebSocket connection status."""
    total_connections: int
    recording_connections: int
    monitoring_connections: int
    debug_connections: int
    connection_details: List[Dict[str, Any]] = []


class LogEntry(BaseModel):
    """Log entry for debugging."""
    timestamp: str
    level: str
    module: str
    message: str
    context: Optional[Dict[str, Any]] = None


class DebugSession:
    """Manages debug session state and metrics collection."""

    def __init__(self):
        self.start_time = time.time()
        self.metrics_history = []
        self.error_count = 0
        self.warning_count = 0
        self.last_error = None
        self.performance_alerts = []

    def collect_system_metrics(self) -> SystemMetrics:
        """Collect current system performance metrics."""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')

            return SystemMetrics(
                cpu_percent=cpu_percent,
                memory_percent=memory.percent,
                memory_available_mb=memory.available / 1024 / 1024,
                disk_free_gb=disk.free / 1024 / 1024 / 1024,
                uptime_seconds=time.time() - self.start_time,
                python_version=f"{psutil.version_info[0]}.{psutil.version_info[1]}.{psutil.version_info[2]}",
                process_count=len(psutil.pids())
            )
        except Exception as e:
            logger.error(f"Error collecting system metrics: {e}")
            return SystemMetrics(
                cpu_percent=0.0,
                memory_percent=0.0,
                memory_available_mb=0.0,
                disk_free_gb=0.0,
                uptime_seconds=0.0,
                python_version="unknown",
                process_count=0
            )

    def collect_audio_status(self) -> AudioSystemStatus:
        """Collect audio system status."""
        try:
            # Mock audio system check - in real implementation, this would use actual audio modules
            from ..module3_phone import DeviceManager

            blackhole_available = DeviceManager.is_blackhole_installed()
            devices = DeviceManager.list_devices()

            input_devices = [d for d in devices if d.get('is_input')]
            output_devices = [d for d in devices if d.get('is_output')]

            default_input = DeviceManager.get_default_input_device()
            default_output = DeviceManager.get_default_output_device()

            return AudioSystemStatus(
                blackhole_available=blackhole_available,
                input_devices_count=len(input_devices),
                output_devices_count=len(output_devices),
                default_input=default_input.get('name') if default_input else None,
                default_output=default_output.get('name') if default_output else None,
                sample_rates_supported=[44100, 48000]
            )

        except Exception as e:
            logger.error(f"Error collecting audio status: {e}")
            return AudioSystemStatus(
                blackhole_available=False,
                input_devices_count=0,
                output_devices_count=0
            )

    def collect_recording_status(self) -> RecordingSystemStatus:
        """Collect recording system status."""
        try:
            # Mock recording status - in real implementation, this would query actual recording state
            return RecordingSystemStatus(
                active_sessions=0,
                total_sessions=0,
                recording_in_progress=False,
                recordings_today=0
            )

        except Exception as e:
            logger.error(f"Error collecting recording status: {e}")
            return RecordingSystemStatus(
                active_sessions=0,
                total_sessions=0,
                recording_in_progress=False,
                recordings_today=0
            )

    def collect_websocket_status(self) -> WebSocketStatus:
        """Collect WebSocket connection status."""
        try:
            stats = connection_manager.get_connection_stats()
            return WebSocketStatus(
                total_connections=stats.get("total_connections", 0),
                recording_connections=stats.get("recording_connections", 0),
                monitoring_connections=stats.get("monitoring_connections", 0),
                debug_connections=stats.get("debug_connections", 0),
                connection_details=stats.get("connection_details", [])
            )

        except Exception as e:
            logger.error(f"Error collecting WebSocket status: {e}")
            return WebSocketStatus(
                total_connections=0,
                recording_connections=0,
                monitoring_connections=0,
                debug_connections=0
            )

    def add_performance_alert(self, message: str, severity: str = "warning"):
        """Add a performance alert."""
        alert = {
            "timestamp": datetime.now().isoformat(),
            "message": message,
            "severity": severity
        }
        self.performance_alerts.append(alert)

        # Keep only last 50 alerts
        if len(self.performance_alerts) > 50:
            self.performance_alerts = self.performance_alerts[-50:]

    def check_performance_thresholds(self, metrics: SystemMetrics):
        """Check performance metrics against thresholds and generate alerts."""
        if metrics.cpu_percent > 80:
            self.add_performance_alert(f"High CPU usage: {metrics.cpu_percent:.1f}%", "warning")

        if metrics.memory_percent > 85:
            self.add_performance_alert(f"High memory usage: {metrics.memory_percent:.1f}%", "warning")

        if metrics.disk_free_gb < 1.0:
            self.add_performance_alert(f"Low disk space: {metrics.disk_free_gb:.1f}GB remaining", "error")


# Global debug session
debug_session = DebugSession()


@debug_router.get("/", response_class=HTMLResponse)
async def debug_dashboard(request: Request):
    """Render the debug dashboard page."""
    return templates.TemplateResponse(
        "debug_dashboard.html",
        {
            "request": request,
            "title": "Debug Dashboard - Phone Recording System"
        }
    )


@debug_router.get("/api/system_metrics")
async def get_system_metrics():
    """Get current system performance metrics."""
    try:
        metrics = debug_session.collect_system_metrics()
        debug_session.check_performance_thresholds(metrics)

        # Add to history
        metrics_dict = metrics.dict()
        metrics_dict["timestamp"] = datetime.now().isoformat()
        debug_session.metrics_history.append(metrics_dict)

        # Keep only last 100 entries
        if len(debug_session.metrics_history) > 100:
            debug_session.metrics_history = debug_session.metrics_history[-100:]

        return JSONResponse({
            "success": True,
            "data": metrics.dict(),
            "timestamp": datetime.now().isoformat()
        })

    except Exception as e:
        logger.error(f"Error getting system metrics: {e}")
        return JSONResponse({
            "success": False,
            "error": str(e)
        }, status_code=500)


@debug_router.get("/api/audio_status")
async def get_audio_status():
    """Get audio system status."""
    try:
        status = debug_session.collect_audio_status()

        return JSONResponse({
            "success": True,
            "data": status.dict(),
            "timestamp": datetime.now().isoformat()
        })

    except Exception as e:
        logger.error(f"Error getting audio status: {e}")
        return JSONResponse({
            "success": False,
            "error": str(e)
        }, status_code=500)


@debug_router.get("/api/recording_status")
async def get_recording_status():
    """Get recording system status."""
    try:
        status = debug_session.collect_recording_status()

        return JSONResponse({
            "success": True,
            "data": status.dict(),
            "timestamp": datetime.now().isoformat()
        })

    except Exception as e:
        logger.error(f"Error getting recording status: {e}")
        return JSONResponse({
            "success": False,
            "error": str(e)
        }, status_code=500)


@debug_router.get("/api/websocket_status")
async def get_websocket_status():
    """Get WebSocket connection status."""
    try:
        status = debug_session.collect_websocket_status()

        return JSONResponse({
            "success": True,
            "data": status.dict(),
            "timestamp": datetime.now().isoformat()
        })

    except Exception as e:
        logger.error(f"Error getting WebSocket status: {e}")
        return JSONResponse({
            "success": False,
            "error": str(e)
        }, status_code=500)


@debug_router.get("/api/performance_alerts")
async def get_performance_alerts():
    """Get performance alerts."""
    try:
        return JSONResponse({
            "success": True,
            "data": {
                "alerts": debug_session.performance_alerts,
                "alert_count": len(debug_session.performance_alerts),
                "error_count": debug_session.error_count,
                "warning_count": debug_session.warning_count
            },
            "timestamp": datetime.now().isoformat()
        })

    except Exception as e:
        logger.error(f"Error getting performance alerts: {e}")
        return JSONResponse({
            "success": False,
            "error": str(e)
        }, status_code=500)


@debug_router.get("/api/metrics_history")
async def get_metrics_history(hours: int = 1):
    """Get historical metrics data."""
    try:
        cutoff_time = datetime.now() - timedelta(hours=hours)

        # Filter metrics by time range
        filtered_metrics = []
        for metric in debug_session.metrics_history:
            metric_time = datetime.fromisoformat(metric["timestamp"])
            if metric_time >= cutoff_time:
                filtered_metrics.append(metric)

        return JSONResponse({
            "success": True,
            "data": {
                "metrics": filtered_metrics,
                "count": len(filtered_metrics),
                "time_range_hours": hours
            },
            "timestamp": datetime.now().isoformat()
        })

    except Exception as e:
        logger.error(f"Error getting metrics history: {e}")
        return JSONResponse({
            "success": False,
            "error": str(e)
        }, status_code=500)


@debug_router.get("/api/log_entries")
async def get_log_entries(level: str = "INFO", limit: int = 100):
    """Get recent log entries."""
    try:
        # In a real implementation, this would read from log files or a log buffer
        # For now, we'll create mock log entries
        mock_logs = [
            LogEntry(
                timestamp=datetime.now().isoformat(),
                level="INFO",
                module="debug_routes",
                message="Debug dashboard accessed",
                context={"user_agent": "Mock Browser", "ip": "127.0.0.1"}
            ),
            LogEntry(
                timestamp=(datetime.now() - timedelta(minutes=1)).isoformat(),
                level="DEBUG",
                module="websocket_routes",
                message="WebSocket connection established",
                context={"client_id": "web_client_123", "type": "recording"}
            ),
            LogEntry(
                timestamp=(datetime.now() - timedelta(minutes=2)).isoformat(),
                level="WARNING",
                module="phone_routes",
                message="BlackHole not detected, using mock audio",
                context={"check_method": "system_profiler"}
            )
        ]

        # Filter by level if specified
        if level != "ALL":
            mock_logs = [log for log in mock_logs if log.level == level]

        # Limit results
        mock_logs = mock_logs[:limit]

        return JSONResponse({
            "success": True,
            "data": {
                "logs": [log.dict() for log in mock_logs],
                "count": len(mock_logs),
                "level_filter": level,
                "limit": limit
            },
            "timestamp": datetime.now().isoformat()
        })

    except Exception as e:
        logger.error(f"Error getting log entries: {e}")
        return JSONResponse({
            "success": False,
            "error": str(e)
        }, status_code=500)


@debug_router.get("/api/system_info")
async def get_system_info():
    """Get comprehensive system information."""
    try:
        import platform
        import sys

        # System information
        system_info = {
            "platform": platform.system(),
            "platform_version": platform.release(),
            "architecture": platform.machine(),
            "python_version": sys.version,
            "python_executable": sys.executable,
            "working_directory": os.getcwd(),
            "environment_variables": {
                "PATH": os.environ.get("PATH", ""),
                "PYTHONPATH": os.environ.get("PYTHONPATH", ""),
                "HOME": os.environ.get("HOME", ""),
                "USER": os.environ.get("USER", "")
            }
        }

        # Process information
        current_process = psutil.Process()
        process_info = {
            "pid": current_process.pid,
            "name": current_process.name(),
            "create_time": datetime.fromtimestamp(current_process.create_time()).isoformat(),
            "cpu_percent": current_process.cpu_percent(),
            "memory_info": current_process.memory_info()._asdict(),
            "num_threads": current_process.num_threads(),
            "open_files": len(current_process.open_files()),
            "connections": len(current_process.connections())
        }

        # Audio system check
        audio_info = debug_session.collect_audio_status()

        return JSONResponse({
            "success": True,
            "data": {
                "system": system_info,
                "process": process_info,
                "audio": audio_info.dict(),
                "debug_session": {
                    "start_time": datetime.fromtimestamp(debug_session.start_time).isoformat(),
                    "uptime_seconds": time.time() - debug_session.start_time,
                    "error_count": debug_session.error_count,
                    "warning_count": debug_session.warning_count
                }
            },
            "timestamp": datetime.now().isoformat()
        })

    except Exception as e:
        logger.error(f"Error getting system info: {e}")
        return JSONResponse({
            "success": False,
            "error": str(e)
        }, status_code=500)


@debug_router.post("/api/clear_alerts")
async def clear_performance_alerts():
    """Clear all performance alerts."""
    try:
        debug_session.performance_alerts.clear()
        debug_session.error_count = 0
        debug_session.warning_count = 0

        return JSONResponse({
            "success": True,
            "message": "Performance alerts cleared",
            "timestamp": datetime.now().isoformat()
        })

    except Exception as e:
        logger.error(f"Error clearing alerts: {e}")
        return JSONResponse({
            "success": False,
            "error": str(e)
        }, status_code=500)


@debug_router.post("/api/test_recording")
async def test_recording_system():
    """Test the recording system functionality."""
    try:
        test_results = {
            "audio_devices": None,
            "blackhole_status": None,
            "websocket_connection": None,
            "api_endpoints": None
        }

        # Test audio devices
        try:
            audio_status = debug_session.collect_audio_status()
            test_results["audio_devices"] = {
                "success": True,
                "blackhole_available": audio_status.blackhole_available,
                "device_count": audio_status.input_devices_count + audio_status.output_devices_count
            }
        except Exception as e:
            test_results["audio_devices"] = {"success": False, "error": str(e)}

        # Test WebSocket connections
        try:
            ws_status = debug_session.collect_websocket_status()
            test_results["websocket_connection"] = {
                "success": True,
                "total_connections": ws_status.total_connections
            }
        except Exception as e:
            test_results["websocket_connection"] = {"success": False, "error": str(e)}

        # Test API endpoints
        test_results["api_endpoints"] = {
            "success": True,
            "endpoints_tested": ["/api/phone/devices", "/debug/api/system_metrics"]
        }

        # Overall test result
        all_tests_passed = all(
            result.get("success", False) for result in test_results.values()
            if result is not None
        )

        return JSONResponse({
            "success": True,
            "data": {
                "overall_result": all_tests_passed,
                "test_results": test_results,
                "test_time": datetime.now().isoformat()
            }
        })

    except Exception as e:
        logger.error(f"Error testing recording system: {e}")
        return JSONResponse({
            "success": False,
            "error": str(e)
        }, status_code=500)


@debug_router.get("/api/health_check")
async def health_check():
    """Comprehensive health check for the system."""
    try:
        health_status = {
            "overall": "healthy",
            "checks": {},
            "timestamp": datetime.now().isoformat()
        }

        # System metrics check
        try:
            metrics = debug_session.collect_system_metrics()
            cpu_healthy = metrics.cpu_percent < 90
            memory_healthy = metrics.memory_percent < 90
            disk_healthy = metrics.disk_free_gb > 0.5

            health_status["checks"]["system"] = {
                "status": "healthy" if all([cpu_healthy, memory_healthy, disk_healthy]) else "warning",
                "cpu_ok": cpu_healthy,
                "memory_ok": memory_healthy,
                "disk_ok": disk_healthy,
                "details": metrics.dict()
            }
        except Exception as e:
            health_status["checks"]["system"] = {"status": "error", "error": str(e)}

        # Audio system check
        try:
            audio_status = debug_session.collect_audio_status()
            audio_healthy = audio_status.input_devices_count > 0 and audio_status.output_devices_count > 0

            health_status["checks"]["audio"] = {
                "status": "healthy" if audio_healthy else "warning",
                "devices_available": audio_healthy,
                "blackhole_available": audio_status.blackhole_available,
                "details": audio_status.dict()
            }
        except Exception as e:
            health_status["checks"]["audio"] = {"status": "error", "error": str(e)}

        # WebSocket check
        try:
            ws_status = debug_session.collect_websocket_status()
            ws_healthy = True  # WebSocket is optional

            health_status["checks"]["websocket"] = {
                "status": "healthy",
                "connections": ws_status.total_connections,
                "details": ws_status.dict()
            }
        except Exception as e:
            health_status["checks"]["websocket"] = {"status": "error", "error": str(e)}

        # Determine overall health
        check_statuses = [check.get("status", "error") for check in health_status["checks"].values()]
        if "error" in check_statuses:
            health_status["overall"] = "error"
        elif "warning" in check_statuses:
            health_status["overall"] = "warning"

        return JSONResponse(health_status)

    except Exception as e:
        logger.error(f"Error in health check: {e}")
        return JSONResponse({
            "overall": "error",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }, status_code=500)


# Background task to collect metrics periodically
async def metrics_collector_task():
    """Background task to collect metrics periodically."""
    while True:
        try:
            # Collect metrics every 30 seconds
            await asyncio.sleep(30)

            metrics = debug_session.collect_system_metrics()
            debug_session.check_performance_thresholds(metrics)

            # Broadcast metrics to debug WebSocket clients
            await connection_manager.broadcast_to_debug({
                "type": "metrics_update",
                "data": metrics.dict(),
                "timestamp": datetime.now().isoformat()
            })

        except asyncio.CancelledError:
            logger.info("Metrics collector task cancelled")
            break
        except Exception as e:
            logger.error(f"Error in metrics collector: {e}")


# Initialize metrics collection on startup
@debug_router.on_event("startup")
async def start_metrics_collection():
    """Start background metrics collection."""
    asyncio.create_task(metrics_collector_task())
    logger.info("Debug metrics collection started")