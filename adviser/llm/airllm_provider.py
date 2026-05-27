"""
AirLLM Tier 3 Provider for Adviser.
Allows running large models (70B+) on consumer GPUs (e.g. 4GB VRAM) via layer-wise inference.
"""

from typing import Any, Optional

try:
    from airllm import AutoModel  # type: ignore
except ImportError:
    AutoModel = None

_AIRLLM_INSTANCE: Any = None
_CURRENT_MODEL_ID: Optional[str] = None


def is_airllm_available() -> bool:
    return AutoModel is not None


def get_airllm(model_id: str) -> Any:
    global _AIRLLM_INSTANCE, _CURRENT_MODEL_ID

    if _AIRLLM_INSTANCE is not None and _CURRENT_MODEL_ID == model_id:
        return _AIRLLM_INSTANCE

    if not is_airllm_available():
        raise RuntimeError(
            "AirLLM is not installed. Install it with: pip install airllm"
        )

    _AIRLLM_INSTANCE = AutoModel.from_pretrained(model_id)
    _CURRENT_MODEL_ID = model_id
    return _AIRLLM_INSTANCE


def generate_chat(
    model_id: str, messages: list[dict[str, Any]], max_tokens: int = 512
) -> str:
    """Generate a chat response using AirLLM."""
    model = get_airllm(model_id)

    # Simple prompt formatting since AirLLM doesn't have a chat template builder built-in
    # This assumes Llama-like format
    prompt = ""
    for msg in messages:
        role = str(msg["role"])
        content = str(msg["content"])
        prompt += f"<|start_header_id|>{role}<|end_header_id|>\n\n{content}<|eot_id|>\n"
    prompt += "<|start_header_id|>assistant<|end_header_id|>\n\n"

    input_tokens = model.tokenizer(
        prompt,
        return_tensors="pt",
        return_attention_mask=False,
        truncation=True,
        max_length=4096,
    )

    generation_output = model.generate(
        input_tokens["input_ids"].cuda(),
        max_new_tokens=max_tokens,
        use_cache=True,
        return_dict_in_generate=True,
    )

    output = str(model.tokenizer.decode(generation_output.sequences[0]))

    # Extract just the assistant's reply
    reply = output.split("<|start_header_id|>assistant<|end_header_id|>\n\n")[-1]
    reply = reply.split("<|eot_id|>")[0].strip()
    return reply
