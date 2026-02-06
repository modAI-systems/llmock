"""OpenAI Model object schemas.

Model is imported from the openai library.
ModelList is defined locally as OpenAI uses pagination wrappers.
"""

from typing import Literal

from openai.types import Model
from pydantic import BaseModel, Field


class ModelList(BaseModel):
    """List of model objects."""

    object: Literal["list"] = Field(
        default="list",
        description='The object type, which is always "list".',
    )
    data: list[Model] = Field(description="List of model objects.")
