"""OpenAI Model object schemas."""

from typing import Literal

from pydantic import BaseModel, Field


class Model(BaseModel):
    """Describes an OpenAI model offering that can be used with the API."""

    id: str = Field(
        description="The model identifier, which can be referenced in the API endpoints."
    )
    object: Literal["model"] = Field(
        default="model",
        description='The object type, which is always "model".',
    )
    created: int = Field(
        description="The Unix timestamp (in seconds) when the model was created."
    )
    owned_by: str = Field(description="The organization that owns the model.")


class ModelList(BaseModel):
    """List of model objects."""

    object: Literal["list"] = Field(
        default="list",
        description='The object type, which is always "list".',
    )
    data: list[Model] = Field(description="List of model objects.")
