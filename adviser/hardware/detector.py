import platform
import subprocess
import json
from dataclasses import dataclass
import psutil
from typing import Any, Optional


@dataclass
class HardwareProfile:
    cpu_name: str
    cpu_cores: int
    ram_gb: float
    gpu_name: Optional[str]
    vram_gb: Optional[float]
    gpu_backend: str
    tier: str
    max_model_gb: float
    recommended_embeds: list[str]
    recommended_llms: dict[str, list[str]]
    recommended_providers: list[str]


def _detect_nvidia() -> Optional[dict[str, Any]]:
    try:
        output = subprocess.check_output(
            ["nvidia-smi", "--query-gpu=name,memory.total", "--format=csv,noheader"],
            stderr=subprocess.DEVNULL,
            text=True,
        )
        if output.strip():
            parts = output.strip().split(", ")
            name = parts[0]
            vram_mb = int(parts[1].replace(" MiB", ""))
            return {"name": name, "vram_gb": vram_mb / 1024.0, "backend": "cuda"}
    except (FileNotFoundError, subprocess.CalledProcessError):
        pass
    return None


def _detect_apple() -> Optional[dict[str, Any]]:
    if platform.system() != "Darwin":
        return None
    try:
        output = subprocess.check_output(
            ["system_profiler", "SPDisplaysDataType", "-json"],
            stderr=subprocess.DEVNULL,
            text=True,
        )
        data = json.loads(output)
        for item in data.get("SPDisplaysDataType", []):
            if (
                "sppci_model" in item
                or "spdisplays_device-id" in item
                or "Apple" in item.get("sppci_model", "")
            ):
                name = item.get("sppci_model", "Apple Silicon")
                # Unified memory on Apple Silicon means RAM = VRAM
                return {"name": name, "vram_gb": None, "backend": "metal"}
    except (FileNotFoundError, subprocess.CalledProcessError, json.JSONDecodeError):
        pass
    return None


def _detect_amd() -> Optional[dict[str, Any]]:
    try:
        output = subprocess.check_output(
            ["rocm-smi", "--showmeminfo", "vram", "--json"],
            stderr=subprocess.DEVNULL,
            text=True,
        )
        data = json.loads(output)
        # Simplified rocm parsing
        for key, info in data.items():
            if key.startswith("card"):
                vram_bytes = int(info.get("VRAM Total Memory (B)", 0))
                return {
                    "name": "AMD Radeon",
                    "vram_gb": vram_bytes / (1024**3),
                    "backend": "rocm",
                }
    except (FileNotFoundError, subprocess.CalledProcessError, json.JSONDecodeError):
        pass
    return None


def detect() -> HardwareProfile:
    cpu_name = platform.processor() or "Unknown CPU"
    cpu_cores = psutil.cpu_count(logical=False) or 1
    ram_gb = psutil.virtual_memory().total / (1024**3)

    gpu_info = _detect_nvidia() or _detect_apple() or _detect_amd()

    if gpu_info:
        gpu_name = gpu_info["name"]
        vram_gb = gpu_info["vram_gb"]
        gpu_backend = gpu_info["backend"]
    else:
        gpu_name = None
        vram_gb = None
        gpu_backend = "cpu"

    effective_mem = vram_gb if vram_gb is not None else ram_gb

    if gpu_backend == "metal":
        max_model_gb = effective_mem * 0.70
    else:
        max_model_gb = effective_mem * 0.80

    if effective_mem < 6.0:
        tier = "LOW"
        recommended_providers = ["cloud", "airllm"]
    elif effective_mem < 12.0:
        tier = "MEDIUM"
        recommended_providers = ["cloud", "ollama", "airllm"]
    elif effective_mem < 20.0:
        tier = "MEDIUM-HIGH"
        recommended_providers = ["cloud", "ollama", "airllm"]
    else:
        tier = "HIGH"
        recommended_providers = ["cloud", "ollama", "airllm"]

    from adviser.hardware.models import get_recommendations

    embeds, llms = get_recommendations(max_model_gb)

    return HardwareProfile(
        cpu_name=cpu_name,
        cpu_cores=cpu_cores,
        ram_gb=round(ram_gb, 1),
        gpu_name=gpu_name,
        vram_gb=round(vram_gb, 1) if vram_gb is not None else None,
        gpu_backend=gpu_backend,
        tier=tier,
        max_model_gb=round(max_model_gb, 1),
        recommended_embeds=embeds,
        recommended_llms=llms,
        recommended_providers=recommended_providers,
    )
