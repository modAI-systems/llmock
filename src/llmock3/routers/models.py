"""OpenAI Models API endpoints."""

from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, status

from llmock3.config import Config, get_config
from llmock3.schemas.models import Model, ModelList

router = APIRouter(prefix="/v1", tags=["models"])


def get_models_config(config: Config) -> list[dict[str, Any]]:
    """Extract models list from config."""
    return config.get("models", [])


@router.get("/models", response_model=ModelList)
async def list_models(
    config: Annotated[Config, Depends(get_config)],
) -> ModelList:
    """List the currently available models.

    Lists the currently available models, and provides basic information
    about each one such as the owner and availability.
    """
    models_config = get_models_config(config)
    models = [
        Model(
            id=m["id"],
            created=m["created"],
            owned_by=m["owned_by"],
        )
        for m in models_config
    ]
    return ModelList(data=models)


@router.get("/models/{model_id}", response_model=Model)
async def retrieve_model(
    model_id: str,
    config: Annotated[Config, Depends(get_config)],
) -> Model:
    """Retrieve a model instance.

    Retrieves a model instance, providing basic information about the model
    such as the owner and permissioning.
    """
    models_config = get_models_config(config)
    for m in models_config:
        if m["id"] == model_id:
            return Model(
                id=m["id"],
                created=m["created"],
                owned_by=m["owned_by"],
            )

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail={
            "error": {
                "message": f"The model '{model_id}' does not exist",
                "type": "invalid_request_error",
                "param": "model",
                "code": "model_not_found",
            }
        },
    )
