"""
Pydantic models for video and audio sidecar JSON files.
"""

from typing import List, Literal, Optional

from pydantic import BaseModel, Field

from .config import MODEL


class VideoSegment(BaseModel):
    start_sec: float
    end_sec: float
    type: Literal["a-roll", "b-roll"] = Field(
        description="a-roll = speech/interview, b-roll = visual/cutaway"
    )
    description: str = Field(
        description="Transcript for a-roll, visual description for b-roll"
    )
    camera_movement: Optional[str] = Field(
        default=None,
        description="Static, Pan, Tilt, Dolly, Handheld, Tracking, Crane, etc.",
    )
    quality_score: int = Field(
        default=5,
        description="1-10.  Focus, stability, exposure, content value.",
    )
    is_good_take: Optional[bool] = Field(
        default=None,
        description="For a-roll: true = usable take, false = bad take / false start",
    )
    filler_words: Optional[List[str]] = Field(
        default=None,
        description="Filler words detected in a-roll segments (um, uh, like, ...)",
    )
    tags: List[str] = Field(default_factory=list)


class VideoSidecar(BaseModel):
    filename: str
    file_path: str
    media_type: str = "video"
    analysis_model: str = MODEL
    fps: float = 24.0
    duration: float = 0.0
    segments: List[VideoSegment] = Field(default_factory=list)


class AudioSection(BaseModel):
    start_sec: float
    end_sec: float
    description: str = Field(
        description="What happens musically: verse, chorus, drop, buildup, breakdown, outro, etc."
    )
    energy: int = Field(
        default=5,
        description="1-10 energy level. 1 = ambient/quiet, 10 = peak intensity",
    )
    bpm_estimate: Optional[float] = Field(
        default=None, description="Estimated BPM for this section"
    )
    mood: Optional[str] = Field(
        default=None, description="Emotional character: uplifting, dark, chill, aggressive, etc."
    )
    tags: List[str] = Field(default_factory=list)


class AudioSidecar(BaseModel):
    filename: str
    file_path: str
    media_type: str = "audio"
    analysis_model: str = MODEL
    duration: float = 0.0
    bpm: Optional[float] = Field(default=None, description="Overall estimated BPM")
    key: Optional[str] = Field(default=None, description="Musical key if detectable")
    genre: Optional[str] = None
    sections: List[AudioSection] = Field(default_factory=list)
