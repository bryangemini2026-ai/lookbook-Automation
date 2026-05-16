# Engagement Report Tool

## Purpose
Analyze SNS engagement metrics and generate performance reports.

## Agent
analyst (데이터 — Data Analyst)

## Input
- `platform`: target platform (instagram, tiktok, twitter)
- `period`: analysis period (7d, 30d, 90d)
- `job_id`: optional specific job to analyze

## Output
- Engagement metrics (likes, views, comments, shares, CTR)
- Performance comparison (vs average, vs previous period)
- Recommendations

## Usage
```python
from tool_seeds import load_tool
tool = load_tool("analyst", "engagement_report")
result = tool.run(platform="instagram", period="7d")
```
