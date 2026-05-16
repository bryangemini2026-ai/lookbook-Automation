from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class JobCreate(BaseModel):
    type: str = "lookbook"
    prompt: str
    negative_prompt: str = ""
    workflow: str = "lookbook_portrait"
    params: dict = Field(default_factory=lambda: {
        "steps": 25,
        "cfg": 7.0,
        "width": 1024,
        "height": 1024,
        "seed": -1,
    })
    upscale: bool = True
    face_fix: bool = False
    make_reel: bool = False
    reel_style: str = "zoom_pan"
    platforms: list[str] = Field(default_factory=lambda: ["instagram"])


class JobResponse(BaseModel):
    id: str
    status: str


class JobDetail(BaseModel):
    id: str
    status: str
    type: str
    prompt: Optional[str] = None
    negative_prompt: Optional[str] = None
    workflow: Optional[str] = None
    params: Optional[str] = None
    result_urls: Optional[str] = None
    error: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
