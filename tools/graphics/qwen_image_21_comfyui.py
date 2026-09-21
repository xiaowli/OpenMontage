"""Qwen-Image-2.1 text-to-image via a local ComfyUI server (OpenMontage tool).

Bundled workflow: Qwen-Image-2.1 7B BF16 DiT + Qwen3-VL 8B INT8 ConvRot
encoder (official 16GB-card combo) + BF16 VAE. Validated on RTX 5070 Ti
16G with ComfyUI 0.37.0 (E:\\AI\\ComfyUI-2.1, scheduled task ComfyUI_21,
port 8188).
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

from tools.base_tool import (
    BaseTool,
    Determinism,
    ExecutionMode,
    ResourceProfile,
    RetryPolicy,
    ToolResult,
    ToolRuntime,
    ToolStability,
    ToolStatus,
    ToolTier,
)
from tools._comfyui.client import ComfyUIClient, ComfyUIError
from tools._comfyui.metadata import (
    BUNDLED_MODEL_STACKS,
    COMFYUI_SETUP_OFFER,
    missing_models_payload,
    model_stack,
    workflow_hash,
)

_WORKFLOWS = Path(__file__).resolve().parent.parent / "_comfyui" / "workflows"

# Models required by the bundled qwen21-txt2img workflow
_REQUIRED_MODELS = [
    "qwen_image_2.1_bf16.safetensors",
    "qwen3vl_8b_int8_convrot.safetensors",
    "qwen_image_2.1_vae_bf16.safetensors",
]
