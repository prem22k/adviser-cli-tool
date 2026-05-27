BYTES_PER_PARAM = {
    "FP32": 4.00,
    "FP16": 2.00,
    "BF16": 2.00,
    "Q8_0": 1.05,
    "Q6_K": 0.75,
    "Q5_K_M": 0.67,
    "Q4_K_M": 0.58,
    "Q3_K": 0.48,
    "Q2_K": 0.34,
}


def estimate_vram_gb(
    params_b: float,
    quant: str = "Q4_K_M",
    active_params_b: float | None = None,
    expert_count: int | None = None,
    experts_active_per_token: int | None = None,
) -> float:
    """Estimate VRAM needed for a model given parameter count in billions and quantization."""
    if active_params_b is not None:
        effective_params_b = active_params_b
    elif expert_count is not None and experts_active_per_token is not None:
        effective_params_b = params_b * (experts_active_per_token / expert_count)
    else:
        effective_params_b = params_b

    bpp = BYTES_PER_PARAM.get(quant.upper(), 0.58)
    return (effective_params_b * 1e9 * bpp) / (1024**3)


def fits_in_memory(
    params_b: float,
    available_gb: float,
    quant: str = "Q4_K_M",
    active_params_b: float | None = None,
    expert_count: int | None = None,
    experts_active_per_token: int | None = None,
) -> bool:
    """Returns True if the model fits in available memory with 15% headroom."""
    return estimate_vram_gb(
        params_b, quant, active_params_b, expert_count, experts_active_per_token
    ) < (available_gb * 0.85)


import os
from pathlib import Path
from typing import Any
from ruamel.yaml import YAML


def _load_catalog() -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    catalog_path = Path(__file__).parent / "catalog.yaml"
    if not catalog_path.exists():
        return [], []

    yaml = YAML(typ="safe")
    with open(catalog_path, "r", encoding="utf-8") as f:
        data = yaml.load(f)

    if not data:
        return [], []

    return data.get("llm_catalog", []), data.get("embed_catalog", [])


def get_recommendations(
    available_gb: float, quant: str = "Q4_K_M"
) -> tuple[list[str], dict[str, list[str]]]:
    """Get recommended embedding models and LLMs that fit in available memory."""
    llm_catalog, embed_catalog = _load_catalog()

    embeds = []
    for m in embed_catalog:
        params_b = float(str(m.get("params_b", 0)))
        active_params_b = (
            float(str(m["active_params_b"])) if "active_params_b" in m else None
        )
        expert_count = int(str(m["expert_count"])) if "expert_count" in m else None
        experts_active = (
            int(str(m["experts_active_per_token"]))
            if "experts_active_per_token" in m
            else None
        )

        if fits_in_memory(
            params_b, available_gb, quant, active_params_b, expert_count, experts_active
        ):
            embeds.append(str(m["id"]))

    llms: dict[str, list[str]] = {}
    for m in llm_catalog:
        params_b = float(str(m.get("params_b", 0)))
        active_params_b = (
            float(str(m["active_params_b"])) if "active_params_b" in m else None
        )
        expert_count = int(str(m["expert_count"])) if "expert_count" in m else None
        experts_active = (
            int(str(m["experts_active_per_token"]))
            if "experts_active_per_token" in m
            else None
        )

        if fits_in_memory(
            params_b, available_gb, quant, active_params_b, expert_count, experts_active
        ):
            cat = str(m["category"])
            if cat not in llms:
                llms[cat] = []
            llms[cat].append(str(m["id"]))

    return embeds, llms
