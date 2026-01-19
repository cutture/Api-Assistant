"""
Template API router.

Provides endpoints for managing and using code templates.
"""

from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from src.api.auth import get_current_user_optional
from src.services.template_service import (
    TemplateService,
    TemplateCategory,
    TemplateLanguage,
    get_template_service,
)


router = APIRouter(prefix="/templates", tags=["templates"])


class TemplateParameterResponse(BaseModel):
    """Response model for a template parameter."""
    name: str
    description: str
    type: str
    required: bool
    default: Optional[Any] = None
    enum_values: Optional[list[str]] = None


class TemplateResponse(BaseModel):
    """Response model for a template."""
    id: str
    name: str
    description: str
    category: str
    language: str
    template_code: str
    test_template: Optional[str] = None
    parameters: list[TemplateParameterResponse]
    tags: list[str]
    usage_count: int
    is_builtin: bool
    created_by: Optional[str] = None
    created_at: str
    updated_at: str


class TemplateListResponse(BaseModel):
    """Response model for template listing."""
    id: str
    name: str
    description: str
    category: str
    language: str
    tags: list[str]
    usage_count: int
    is_builtin: bool


class CreateTemplateRequest(BaseModel):
    """Request to create a new template."""
    name: str = Field(..., min_length=1, max_length=255)
    description: str = Field(..., max_length=1000)
    category: str = Field(..., description="Template category")
    language: str = Field(..., description="Programming language")
    template_code: str = Field(..., description="Template code with placeholders")
    test_template: Optional[str] = Field(None, description="Test template code")
    parameters: Optional[list[dict]] = Field(None, description="Template parameters")
    tags: Optional[list[str]] = Field(None, description="Template tags")


class UpdateTemplateRequest(BaseModel):
    """Request to update a template."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    template_code: Optional[str] = None
    test_template: Optional[str] = None
    tags: Optional[list[str]] = None


class RenderTemplateRequest(BaseModel):
    """Request to render a template."""
    parameters: dict[str, Any] = Field(..., description="Template parameters")


class RenderTemplateResponse(BaseModel):
    """Response from rendering a template."""
    code: str
    tests: Optional[str] = None
    template_id: str
    template_name: str


class CategoryResponse(BaseModel):
    """Response model for a category."""
    id: str
    name: str
    count: int


class LanguageResponse(BaseModel):
    """Response model for a language."""
    id: str
    name: str
    count: int


def _template_to_response(template) -> TemplateResponse:
    """Convert a template to response model."""
    t = template.to_dict()
    return TemplateResponse(
        id=t["id"],
        name=t["name"],
        description=t["description"],
        category=t["category"],
        language=t["language"],
        template_code=t["template_code"],
        test_template=t["test_template"],
        parameters=[TemplateParameterResponse(**p) for p in t["parameters"]],
        tags=t["tags"],
        usage_count=t["usage_count"],
        is_builtin=t["is_builtin"],
        created_by=t["created_by"],
        created_at=t["created_at"],
        updated_at=t["updated_at"],
    )


def _template_to_list_response(template) -> TemplateListResponse:
    """Convert a template to list response model."""
    t = template.to_dict()
    return TemplateListResponse(
        id=t["id"],
        name=t["name"],
        description=t["description"],
        category=t["category"],
        language=t["language"],
        tags=t["tags"],
        usage_count=t["usage_count"],
        is_builtin=t["is_builtin"],
    )


@router.get("", response_model=list[TemplateListResponse])
async def list_templates(
    category: Optional[str] = None,
    language: Optional[str] = None,
    tags: Optional[str] = None,
    template_service: TemplateService = Depends(get_template_service),
) -> list[TemplateListResponse]:
    """
    List available templates with optional filtering.

    - **category**: Filter by category (rest_api, crud, authentication, etc.)
    - **language**: Filter by language (python, javascript, typescript, etc.)
    - **tags**: Comma-separated list of tags to filter by
    """
    cat = None
    if category:
        try:
            cat = TemplateCategory(category)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid category: {category}")

    lang = None
    if language:
        try:
            lang = TemplateLanguage(language)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid language: {language}")

    tag_list = tags.split(",") if tags else None

    templates = template_service.list_templates(
        category=cat,
        language=lang,
        tags=tag_list,
    )

    return [_template_to_list_response(t) for t in templates]


@router.get("/categories", response_model=list[CategoryResponse])
async def get_categories(
    template_service: TemplateService = Depends(get_template_service),
) -> list[CategoryResponse]:
    """Get list of template categories with counts."""
    categories = template_service.get_categories()
    return [CategoryResponse(**c) for c in categories]


@router.get("/languages", response_model=list[LanguageResponse])
async def get_languages(
    template_service: TemplateService = Depends(get_template_service),
) -> list[LanguageResponse]:
    """Get list of supported languages with counts."""
    languages = template_service.get_languages()
    return [LanguageResponse(**l) for l in languages]


@router.get("/{template_id}", response_model=TemplateResponse)
async def get_template(
    template_id: str,
    template_service: TemplateService = Depends(get_template_service),
) -> TemplateResponse:
    """Get a template by ID."""
    template = template_service.get_template(template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    return _template_to_response(template)


@router.post("", response_model=TemplateResponse, status_code=201)
async def create_template(
    request: CreateTemplateRequest,
    user: Optional[dict] = Depends(get_current_user_optional),
    template_service: TemplateService = Depends(get_template_service),
) -> TemplateResponse:
    """
    Create a new custom template.

    Custom templates can be created by users to save reusable code patterns.
    """
    try:
        category = TemplateCategory(request.category)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid category: {request.category}")

    try:
        language = TemplateLanguage(request.language)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid language: {request.language}")

    user_id = user.get("id") if user else None

    template = template_service.create_template(
        name=request.name,
        description=request.description,
        category=category,
        language=language,
        template_code=request.template_code,
        test_template=request.test_template,
        parameters=request.parameters,
        tags=request.tags,
        created_by=user_id,
    )

    return _template_to_response(template)


@router.patch("/{template_id}", response_model=TemplateResponse)
async def update_template(
    template_id: str,
    request: UpdateTemplateRequest,
    user: Optional[dict] = Depends(get_current_user_optional),
    template_service: TemplateService = Depends(get_template_service),
) -> TemplateResponse:
    """
    Update a custom template.

    Only custom templates can be updated. Built-in templates are read-only.
    """
    template = template_service.get_template(template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")

    if template.is_builtin:
        raise HTTPException(status_code=403, detail="Cannot modify built-in templates")

    updates = request.model_dump(exclude_none=True)
    updated = template_service.update_template(template_id, **updates)

    if not updated:
        raise HTTPException(status_code=500, detail="Failed to update template")

    return _template_to_response(updated)


@router.delete("/{template_id}")
async def delete_template(
    template_id: str,
    user: Optional[dict] = Depends(get_current_user_optional),
    template_service: TemplateService = Depends(get_template_service),
) -> dict:
    """
    Delete a custom template.

    Only custom templates can be deleted. Built-in templates cannot be removed.
    """
    template = template_service.get_template(template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")

    if template.is_builtin:
        raise HTTPException(status_code=403, detail="Cannot delete built-in templates")

    success = template_service.delete_template(template_id)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to delete template")

    return {"deleted": True, "template_id": template_id}


@router.post("/{template_id}/render", response_model=RenderTemplateResponse)
async def render_template(
    template_id: str,
    request: RenderTemplateRequest,
    user: Optional[dict] = Depends(get_current_user_optional),
    template_service: TemplateService = Depends(get_template_service),
) -> RenderTemplateResponse:
    """
    Render a template with the provided parameters.

    Replaces placeholders in the template with the provided values.
    """
    template = template_service.get_template(template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")

    # Validate required parameters
    for param in template.parameters:
        if param.required and param.name not in request.parameters:
            if param.default is None:
                raise HTTPException(
                    status_code=400,
                    detail=f"Missing required parameter: {param.name}"
                )

    result = template_service.render_template(template_id, request.parameters)
    if not result:
        raise HTTPException(status_code=500, detail="Failed to render template")

    code, tests = result

    return RenderTemplateResponse(
        code=code,
        tests=tests,
        template_id=template_id,
        template_name=template.name,
    )
