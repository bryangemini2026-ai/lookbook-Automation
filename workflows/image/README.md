# Image Workflow Templates

Place ComfyUI workflow JSON files here.

Expected node naming conventions for parameter injection:

- **Positive Prompt** node: `_meta.title` contains "positive"
- **Negative Prompt** node: `_meta.title` contains "negative"
- **KSampler** node: `class_type` = "KSampler"
- **EmptyLatentImage** node: `class_type` = "EmptyLatentImage"

## Recommended Workflows

| File | Purpose |
|------|---------|
| `lookbook_portrait.json` | Portrait/fashion photography |
| `lookbook_full_body.json` | Full body outfit shots |
| `lookbook_flatlay.json` | Flat lay product photography |
| `lookbook_lifestyle.json` | Lifestyle/editorial shots |
| `upscale_4x.json` | Real-ESRGAN 4x upscale |
| `face_fix.json` | GFPGAN face restoration |

## How to Export from ComfyUI

1. Build your workflow in ComfyUI
2. Set node titles (right-click → Title) to match conventions above
3. Save as API format: `Save (API Format)` button
4. Place JSON file in this directory
