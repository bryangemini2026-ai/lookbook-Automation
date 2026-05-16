import os
import json
import glob

from clients.comfyui import ComfyUIClient


# Workflow template directory
WORKFLOW_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "workflows", "image")


class GenerationModule:
    """Handles image generation via ComfyUI Image server."""

    def __init__(self, comfyui: ComfyUIClient):
        self.comfyui = comfyui

    def generate(self, prompt: str, negative: str, workflow: str, params: dict) -> list[bytes]:
        """
        Generate images using a ComfyUI workflow template.

        Args:
            prompt: Positive prompt
            negative: Negative prompt
            workflow: Workflow name (e.g., 'lookbook_portrait')
            params: Generation parameters (steps, cfg, width, height, seed)

        Returns:
            List of generated image bytes
        """
        template = self._load_workflow(workflow)
        injected = self._inject_params(template, prompt, negative, params)

        print(f"  Generation: workflow={workflow}, {params.get('width', 1024)}x{params.get('height', 1024)}")
        images = self.comfyui.execute_workflow(injected)

        # Free VRAM after generation
        self.comfyui.free_memory()

        return images

    def generate_batch(self, prompt: str, negative: str, workflow: str, params: dict, count: int = 4) -> list[bytes]:
        """
        Generate multiple images SEQUENTIALLY.
        Never use batch_size > 1 on 8GB VRAM.
        """
        images = []
        base_seed = params.get("seed", -1)
        for i in range(count):
            p = params.copy()
            p["seed"] = base_seed + i if base_seed >= 0 else -1
            imgs = self.generate(prompt, negative, workflow, p)
            images.extend(imgs)
        return images

    def _load_workflow(self, name: str) -> dict:
        """Load a workflow JSON template by name."""
        path = os.path.join(WORKFLOW_DIR, f"{name}.json")
        if not os.path.exists(path):
            # Fallback: list available workflows
            available = glob.glob(os.path.join(WORKFLOW_DIR, "*.json"))
            names = [os.path.splitext(os.path.basename(f))[f] for f in available]
            raise FileNotFoundError(f"Workflow '{name}' not found. Available: {names}")
        with open(path) as f:
            return json.load(f)

    def _inject_params(self, template: dict, prompt: str, negative: str, params: dict) -> dict:
        """
        Inject prompt and parameters into workflow template.

        Expects template to have placeholder nodes with _meta.title markers:
        - "Positive Prompt" node: prompt text injected
        - "Negative Prompt" node: negative text injected
        - "KSampler" node: steps, cfg, seed injected
        - "EmptyLatentImage" node: width, height injected
        """
        workflow = json.loads(json.dumps(template))  # deep copy

        for node_id, node in workflow.items():
            if not isinstance(node, dict):
                continue

            title = node.get("_meta", {}).get("title", "").lower()
            class_type = node.get("class_type", "").lower()

            # Inject positive prompt
            if "positive" in title or (class_type == "cliptextencode" and "positive" in title):
                if "inputs" in node and "text" in node["inputs"]:
                    node["inputs"]["text"] = prompt

            # Inject negative prompt
            if "negative" in title or (class_type == "cliptextencode" and "negative" in title):
                if "inputs" in node and "text" in node["inputs"]:
                    node["inputs"]["text"] = negative

            # Inject sampler params
            if class_type == "ksampler":
                if "steps" in params:
                    node["inputs"]["steps"] = params["steps"]
                if "cfg" in params:
                    node["inputs"]["cfg"] = params["cfg"]
                if "seed" in params and params["seed"] >= 0:
                    node["inputs"]["seed"] = params["seed"]

            # Inject resolution
            if class_type == "emptylatentimage":
                if "width" in params:
                    node["inputs"]["width"] = params["width"]
                if "height" in params:
                    node["inputs"]["height"] = params["height"]

        return workflow
