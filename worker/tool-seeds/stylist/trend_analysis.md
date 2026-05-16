# Trend Analysis Tool

## Purpose
Analyze current fashion trends from SNS data and generate style recommendations.

## Agent
stylist (스타 — Head of Style)

## Input
- `keywords`: list of search keywords
- `platforms`: target platforms (instagram, tiktok, pinterest)
- `days`: analysis period (default: 7)

## Output
- Trending hashtags
- Popular styles
- Color palettes
- Recommended themes for lookbook

## Usage
```python
from tool_seeds import load_tool
tool = load_tool("stylist", "trend_analysis")
result = tool.run(keywords=["fashion", "lookbook"], platforms=["instagram"], days=7)
```
