# Lookbook Generate Tool

## Purpose
Generate lookbook images via ComfyUI with optimized prompts.

## Agent
photographer (포토 — Lead Photographer)

## Input
- `prompt`: style description
- `reference_image`: optional reference image path
- `workflow`: ComfyUI workflow preset
- `params`: generation parameters (steps, cfg, resolution)
- `count`: number of images to generate

## Output
- List of generated image paths

## Usage
```python
from tool_seeds import load_tool
tool = load_tool("photographer", "lookbook_generate")
result = tool.run(prompt="minimalist fashion, studio lighting", count=4)
```
