"""Host CPU and memory metrics for the dashboard."""

from __future__ import annotations

from typing import Any

import psutil


def _load_1m() -> float | None:
    try:
        return float(psutil.getloadavg()[0])
    except (AttributeError, OSError):
        return None


def _ollama_rss_bytes() -> int | None:
    total = 0
    found = False
    for proc in psutil.process_iter(["name", "memory_info"]):
        name = (proc.info.get("name") or "").lower()
        if "ollama" not in name and "llama-server" not in name:
            continue
        mem = proc.info.get("memory_info")
        if mem is not None:
            total += mem.rss
            found = True
    return total if found else None


def get_host_metrics(*, sample_cpu: bool = True) -> dict[str, Any]:
    mem = psutil.virtual_memory()
    cpu = psutil.cpu_percent(interval=0.1 if sample_cpu else None)
    load = _load_1m()
    ollama_rss = _ollama_rss_bytes()

    cpu_level = "ok"
    if cpu >= 85 or (load is not None and load >= psutil.cpu_count() * 0.9):
        cpu_level = "warn"
    elif cpu >= 60 or (load is not None and load >= psutil.cpu_count() * 0.6):
        cpu_level = "amber"

    mem_level = "ok"
    if mem.percent >= 90:
        mem_level = "warn"
    elif mem.percent >= 75:
        mem_level = "amber"

    return {
        "cpu_percent": round(cpu, 1),
        "load_1m": round(load, 2) if load is not None else None,
        "cpu_cores": psutil.cpu_count() or 1,
        "cpu_level": cpu_level,
        "memory_used_gb": round(mem.used / (1024**3), 1),
        "memory_total_gb": round(mem.total / (1024**3), 1),
        "memory_percent": round(mem.percent, 1),
        "memory_level": mem_level,
        "ollama_memory_gb": round(ollama_rss / (1024**3), 2) if ollama_rss else None,
    }
