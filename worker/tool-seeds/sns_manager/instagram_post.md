# Instagram Post Tool

## Purpose
Post content to Instagram with optimized caption and hashtags.

## Agent
sns_manager (소셜 — SNS Manager)

## Input
- `image_path`: path to image file
- `caption`: post caption (auto-generated if empty)
- `hashtags`: list of hashtags (auto-generated if empty)
- `schedule_time`: optional ISO timestamp for scheduled posting

## Output
- Post ID or scheduled confirmation

## Usage
```python
from tool_seeds import load_tool
tool = load_tool("sns_manager", "instagram_post")
result = tool.run(image_path="/path/to/image.jpg", caption="New lookbook drop!")
```
