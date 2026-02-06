"""OpenAI Models API endpoints."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from llmock3.config import Settings, get_settings
from llmock3.schemas.models import Model, ModelList

router = APIRouter(prefix="/v1", tags=["models"])


@router.get("/models", response_model=ModelList)
async def list_models(
    settings: Annotated[Settings, Depends(get_settings)],
) -> ModelList:
    """List the currently available models.

    Lists the currently available models, and provides basic information
    about each one such as the owner and availability.
    """
    models = [
        Model(
            id=model_config.id,
            created=model_config.created,
            owned_by=model_config.owned_by,
        )
        for model_config in settings.models
    ]
    return ModelList(data=models)


@router.get("/models/{model_id}", response_model=Model)
async def retrieve_model(
    model_id: str,
    settings: Annotated[Settings, Depends(get_settings)],
) -> Model:
    """Retrieve a model instance.

    Retrieves a model instance, providing basic information about the model
    such as the owner and permissioning.
    """
    for model_config in settings.models:
        if model_config.id == model_id:
            return Model(
                id=model_config.id,
                created=model_config.created,
                owned_by=model_config.owned_by,
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
