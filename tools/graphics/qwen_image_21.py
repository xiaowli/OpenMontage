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


class QwenImage21(BaseTool):
    name = "qwen_image_21"
    version = "0.1.0"
    tier = ToolTier.GENERATE
    capability = "image_generation"
    provider = "comfyui"
    stability = ToolStability.EXPERIMENTAL
    execution_mode = ExecutionMode.SYNC
    determinism = Determinism.SEEDED
    runtime = ToolRuntime.LOCAL_GPU

    dependencies = []  # checked at runtime via server health
    setup_offer = COMFYUI_SETUP_OFFER
    install_instructions = (
        "Start a ComfyUI server and set COMFYUI_SERVER_URL "
        "(default http://localhost:8188).\n"
        "Qwen-Image-2.1 needs: qwen_image_2.1_bf16 (diffusion_models), "
        "qwen3vl_8b_int8_convrot (text_encoders), "
        "qwen_image_2.1_vae_bf16 (vae).\n"
        "Running a separate ComfyUI instance for images? Set COMFYUI_IMAGE_SERVER_URL "
        "instead -- it takes priority over COMFYUI_SERVER_URL for this tool only."
    )
    agent_skills = ["comfyui"]

    capabilities = ["text_to_image"]
    supports = {
        "seed": True,
        "custom_size": True,
        "custom_workflow": True,
        "custom_output_node": True,
        "offline": True,
    }
    best_for = [
        "local GPU generation without API costs",
        "16GB VRAM cards (official INT8 encoder + BF16 DiT combo)",
        "unified generation and editing model family (Qwen)",
    ]
    not_good_for = [
        "setups without a running ComfyUI server",
        "CPU-only machines",
        "cards with <12GB VRAM",
    ]
    fallback = "comfyui_image"
    fallback_tools = ["comfyui_image", "flux_image", "local_diffusion"]

    input_schema = {
        "type": "object",
        "required": ["prompt"],
        "properties": {
            "prompt": {
                "type": "string",
                "description": "Text prompt describing the image to generate.",
            },
            "negative_prompt": {
                "type": "string",
                "description": (
                    "Negative prompt. Defaults to a general quality-negative "
                    "when omitted."
                ),
            },
            "width": {"type": "integer", "minimum": 256, "maximum": 2048},
            "height": {"type": "integer", "minimum": 256, "maximum": 2048},
            "steps": {"type": "integer", "minimum": 4, "maximum": 100},
            "cfg": {"type": "number", "minimum": 1.0, "maximum": 12.0},
            "seed": {"type": "integer"},
            "output_path": {"type": "string"},
            "workflow_json": {"type": "string"},
            "workflow_path": {"type": "string"},
            "output_node": {"type": "string"},
            "workflow_model": {"type": "string"},
            "workflow_model_stack": {"type": "array"},
        },
    }

    output_schema = {
        "type": "object",
        "required": ["provider", "model", "prompt", "output"],
        "properties": {
            "provider": {"type": "string"},
            "model": {"type": "string"},
            "prompt": {"type": "string"},
            "width": {"type": "integer"},
            "height": {"type": "integer"},
            "steps": {"type": "integer"},
            "cfg": {"type": "number"},
            "output": {"type": "string"},
            "format": {"type": "string"},
            "workflow_provenance": {"type": "object"},
        },
    }

    artifact_schema = {
        "type": "object",
        "required": ["path"],
        "properties": {
            "path": {"type": "string"},
            "kind": {"type": "string", "enum": ["image"]},
            "media_type": {"type": "string", "enum": ["image/png"]},
        },
    }

    def __init__(self) -> None:
        self._client = ComfyUIClient(capability="image")

    def get_info(self) -> dict[str, Any]:
        info = super().get_info()
        info["setup_offer"] = self.setup_offer
        info["bundled_model_stack"] = BUNDLED_MODEL_STACKS["qwen21-txt2img"]
        return info

    def execute(self, inputs: dict[str, Any]) -> ToolResult:
        custom_workflow = bool(inputs.get("workflow_json") or inputs.get("workflow_path"))
        if custom_workflow and not inputs.get("output_node"):
            return ToolResult(
                success=False,
                error=(
                    "Custom ComfyUI workflows require output_node so OpenMontage "
                    "knows which ComfyUI node to download artifacts from."
                ),
            )

        if not self._client.is_available():
            return ToolResult(
                success=False,
                error=self._client.unavailable_reason(),
            )

        if not custom_workflow:
            _, missing = self._client.check_models(_REQUIRED_MODELS)
            if missing:
                return ToolResult(
                    success=False,
                    data=missing_models_payload(
                        missing,
                        workflow_key="qwen21-txt2img",
                        workflow_name="qwen21-txt2img.json",
                    ),
                    error=(
                        f"ComfyUI server is running but missing required models: "
                        f"{', '.join(missing)}.\n"
                        f"See data.missing_models for destination hints and download URLs."
                    ),
                )

        start = time.time()
        seed = inputs.get("seed") or ComfyUIClient.random_seed()
        width = inputs.get("width", 1024)
        height = inputs.get("height", 1024)
        steps = inputs.get("steps", 40)
        cfg = inputs.get("cfg", 4.0)
        output_path = Path(inputs.get("output_path", f"qwen21_image_{seed}.png"))

        try:
            if custom_workflow:
                workflow = self._load_custom_workflow(inputs)
                output_node = str(inputs["output_node"])
            else:
                workflow = ComfyUIClient.load_workflow(_WORKFLOWS / "qwen21-txt2img.json")
                workflow = ComfyUIClient.patch_workflow(workflow, {
                    "4": {
                        "prompt": inputs["prompt"],
                        "resolution": min(width, height),
                    },
                    "5": {"width": width, "height": height, "batch_size": 1},
                    "6": {"seed": seed, "steps": steps, "cfg": cfg},
                    "8": {"filename_prefix": output_path.stem},
                })
                output_node = "8"

            provenance = self._workflow_provenance(
                inputs, custom_workflow, output_node, workflow
            )
            paths = self._client.generate(
                workflow, output_node=output_node, dest=output_path, timeout=900,
            )

        except ComfyUIError as exc:
            return ToolResult(success=False, error=str(exc))
        except Exception as exc:
            return ToolResult(success=False, error=f"Qwen-Image-2.1 generation failed: {exc}")

        model_name = self._model_name(inputs, custom_workflow)
        return ToolResult(
            success=True,
            data={
                "provider": "comfyui",
                "model": model_name,
                "prompt": inputs["prompt"],
                "width": width,
                "height": height,
                "steps": steps,
                "cfg": cfg,
                "output": str(paths[0]),
                "format": "png",
                "workflow_provenance": provenance,
            },
            artifacts=[str(p) for p in paths],
            cost_usd=0.0,
            duration_seconds=round(time.time() - start, 2),
            seed=seed,
            model=model_name,
        )

    @staticmethod
    def _load_custom_workflow(inputs: dict[str, Any]) -> dict:
        if inputs.get("workflow_json"):
            return json.loads(inputs["workflow_json"])
        return ComfyUIClient.load_workflow(Path(inputs["workflow_path"]))

    @staticmethod
    def _model_name(inputs: dict[str, Any], custom_workflow: bool) -> str:
        if not custom_workflow:
            return "qwen-image-2.1-bf16"
        return (
            inputs.get("workflow_model")
            or inputs.get("model")
            or inputs.get("workflow_name")
            or "custom-comfyui-workflow"
        )

    @staticmethod
    def _workflow_provenance(
        inputs: dict[str, Any],
        custom_workflow: bool,
        output_node: str,
        workflow: dict[str, Any],
    ) -> dict[str, Any]:
        if not custom_workflow:
            return {
                "source": "bundled",
                "workflow": "qwen21-txt2img.json",
                "workflow_hash_sha256": workflow_hash(workflow),
                "model_stack": model_stack("qwen21-txt2img", inputs),
                "output_node": output_node,
            }
        return {
            "source": "user_supplied",
            "workflow_name": inputs.get("workflow_name"),
            "workflow_path": inputs.get("workflow_path"),
            "model": inputs.get("workflow_model") or inputs.get("model"),
            "workflow_hash_sha256": workflow_hash(workflow),
            "model_stack": model_stack(None, inputs),
            "model_stack_source": (
                "caller_supplied"
                if inputs.get("workflow_model_stack")
                else "unknown_custom_workflow"
            ),
            "output_node": output_node,
        }
