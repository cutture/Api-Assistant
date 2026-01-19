"""
Template Service for code generation templates.

Provides a library of reusable code templates that can be used
as starting points for code generation, with customizable parameters.
"""

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional


class TemplateCategory(str, Enum):
    """Categories of code templates."""
    REST_API = "rest_api"
    CRUD = "crud"
    AUTHENTICATION = "authentication"
    DATABASE = "database"
    TESTING = "testing"
    UTILITY = "utility"
    FRONTEND = "frontend"
    INTEGRATION = "integration"


class TemplateLanguage(str, Enum):
    """Programming languages supported by templates."""
    PYTHON = "python"
    JAVASCRIPT = "javascript"
    TYPESCRIPT = "typescript"
    JAVA = "java"
    GO = "go"
    CSHARP = "csharp"
    ANY = "any"  # Language-agnostic templates


@dataclass
class TemplateParameter:
    """A parameter for a template that can be customized."""
    name: str
    description: str
    param_type: str  # string, number, boolean, list, enum
    required: bool = True
    default: Optional[Any] = None
    enum_values: Optional[list[str]] = None

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "description": self.description,
            "type": self.param_type,
            "required": self.required,
            "default": self.default,
            "enum_values": self.enum_values,
        }


@dataclass
class CodeTemplate:
    """A code template for generation."""
    id: str
    name: str
    description: str
    category: TemplateCategory
    language: TemplateLanguage
    template_code: str
    test_template: Optional[str] = None
    parameters: list[TemplateParameter] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    usage_count: int = 0
    is_builtin: bool = True
    created_by: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "category": self.category.value,
            "language": self.language.value,
            "template_code": self.template_code,
            "test_template": self.test_template,
            "parameters": [p.to_dict() for p in self.parameters],
            "tags": self.tags,
            "usage_count": self.usage_count,
            "is_builtin": self.is_builtin,
            "created_by": self.created_by,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

    def render(self, params: dict[str, Any]) -> str:
        """Render the template with the given parameters."""
        code = self.template_code
        for param in self.parameters:
            placeholder = f"{{{{{param.name}}}}}"
            value = params.get(param.name, param.default)
            if value is not None:
                code = code.replace(placeholder, str(value))
        return code

    def render_tests(self, params: dict[str, Any]) -> Optional[str]:
        """Render the test template with the given parameters."""
        if not self.test_template:
            return None
        tests = self.test_template
        for param in self.parameters:
            placeholder = f"{{{{{param.name}}}}}"
            value = params.get(param.name, param.default)
            if value is not None:
                tests = tests.replace(placeholder, str(value))
        return tests


# Built-in templates
BUILTIN_TEMPLATES: list[CodeTemplate] = [
    # Python REST API Template
    CodeTemplate(
        id="py-rest-api-fastapi",
        name="FastAPI REST API",
        description="A complete FastAPI REST API with endpoints, models, and error handling",
        category=TemplateCategory.REST_API,
        language=TemplateLanguage.PYTHON,
        template_code='''"""
FastAPI REST API for {{resource_name}} management.
"""

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

router = APIRouter(prefix="/{{resource_name_lower}}s", tags=["{{resource_name}}s"])


class {{resource_name}}Base(BaseModel):
    """Base model for {{resource_name}}."""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None


class {{resource_name}}Create({{resource_name}}Base):
    """Model for creating a {{resource_name}}."""
    pass


class {{resource_name}}Update(BaseModel):
    """Model for updating a {{resource_name}}."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None


class {{resource_name}}Response({{resource_name}}Base):
    """Response model for {{resource_name}}."""
    id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# In-memory storage (replace with database in production)
_storage: dict[str, dict] = {}


@router.post("", response_model={{resource_name}}Response, status_code=status.HTTP_201_CREATED)
async def create_{{resource_name_lower}}(data: {{resource_name}}Create) -> {{resource_name}}Response:
    """Create a new {{resource_name}}."""
    import uuid
    item_id = str(uuid.uuid4())
    now = datetime.utcnow()
    item = {
        "id": item_id,
        "name": data.name,
        "description": data.description,
        "created_at": now,
        "updated_at": now,
    }
    _storage[item_id] = item
    return {{resource_name}}Response(**item)


@router.get("", response_model=list[{{resource_name}}Response])
async def list_{{resource_name_lower}}s() -> list[{{resource_name}}Response]:
    """List all {{resource_name}}s."""
    return [{{resource_name}}Response(**item) for item in _storage.values()]


@router.get("/{item_id}", response_model={{resource_name}}Response)
async def get_{{resource_name_lower}}(item_id: str) -> {{resource_name}}Response:
    """Get a {{resource_name}} by ID."""
    if item_id not in _storage:
        raise HTTPException(status_code=404, detail="{{resource_name}} not found")
    return {{resource_name}}Response(**_storage[item_id])


@router.patch("/{item_id}", response_model={{resource_name}}Response)
async def update_{{resource_name_lower}}(item_id: str, data: {{resource_name}}Update) -> {{resource_name}}Response:
    """Update a {{resource_name}}."""
    if item_id not in _storage:
        raise HTTPException(status_code=404, detail="{{resource_name}} not found")
    item = _storage[item_id]
    if data.name is not None:
        item["name"] = data.name
    if data.description is not None:
        item["description"] = data.description
    item["updated_at"] = datetime.utcnow()
    return {{resource_name}}Response(**item)


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_{{resource_name_lower}}(item_id: str) -> None:
    """Delete a {{resource_name}}."""
    if item_id not in _storage:
        raise HTTPException(status_code=404, detail="{{resource_name}} not found")
    del _storage[item_id]
''',
        test_template='''"""Tests for {{resource_name}} API."""

import pytest
from fastapi.testclient import TestClient


def test_create_{{resource_name_lower}}(client: TestClient):
    """Test creating a {{resource_name}}."""
    response = client.post(
        "/{{resource_name_lower}}s",
        json={"name": "Test {{resource_name}}", "description": "Test description"}
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Test {{resource_name}}"
    assert "id" in data


def test_list_{{resource_name_lower}}s(client: TestClient):
    """Test listing {{resource_name}}s."""
    response = client.get("/{{resource_name_lower}}s")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_get_{{resource_name_lower}}_not_found(client: TestClient):
    """Test getting non-existent {{resource_name}}."""
    response = client.get("/{{resource_name_lower}}s/nonexistent-id")
    assert response.status_code == 404
''',
        parameters=[
            TemplateParameter(
                name="resource_name",
                description="Name of the resource (PascalCase, e.g., 'Product')",
                param_type="string",
                required=True,
                default="Item",
            ),
            TemplateParameter(
                name="resource_name_lower",
                description="Lowercase name of the resource (e.g., 'product')",
                param_type="string",
                required=True,
                default="item",
            ),
        ],
        tags=["api", "rest", "fastapi", "crud"],
    ),

    # Python Authentication Template
    CodeTemplate(
        id="py-auth-jwt",
        name="JWT Authentication",
        description="JWT-based authentication with login, register, and token refresh",
        category=TemplateCategory.AUTHENTICATION,
        language=TemplateLanguage.PYTHON,
        template_code='''"""
JWT Authentication module.
"""

import secrets
from datetime import datetime, timedelta
from typing import Optional

import jwt
from passlib.context import CryptContext
from pydantic import BaseModel, EmailStr


# Configuration
SECRET_KEY = "{{secret_key}}"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = {{access_token_expire_minutes}}
REFRESH_TOKEN_EXPIRE_DAYS = {{refresh_token_expire_days}}

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class TokenPayload(BaseModel):
    """JWT token payload."""
    sub: str
    exp: datetime
    type: str  # "access" or "refresh"


class TokenResponse(BaseModel):
    """Token response model."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)


def hash_password(password: str) -> str:
    """Hash a password."""
    return pwd_context.hash(password)


def create_access_token(subject: str) -> str:
    """Create a new access token."""
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {"sub": subject, "exp": expire, "type": "access"}
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def create_refresh_token(subject: str) -> str:
    """Create a new refresh token."""
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    payload = {"sub": subject, "exp": expire, "type": "refresh"}
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def create_tokens(subject: str) -> TokenResponse:
    """Create both access and refresh tokens."""
    return TokenResponse(
        access_token=create_access_token(subject),
        refresh_token=create_refresh_token(subject),
    )


def decode_token(token: str) -> Optional[TokenPayload]:
    """Decode and validate a JWT token."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return TokenPayload(**payload)
    except jwt.PyJWTError:
        return None


def validate_access_token(token: str) -> Optional[str]:
    """Validate an access token and return the subject."""
    payload = decode_token(token)
    if payload and payload.type == "access":
        return payload.sub
    return None


def validate_refresh_token(token: str) -> Optional[str]:
    """Validate a refresh token and return the subject."""
    payload = decode_token(token)
    if payload and payload.type == "refresh":
        return payload.sub
    return None
''',
        parameters=[
            TemplateParameter(
                name="secret_key",
                description="Secret key for JWT signing",
                param_type="string",
                required=True,
                default="your-secret-key-change-in-production",
            ),
            TemplateParameter(
                name="access_token_expire_minutes",
                description="Access token expiration in minutes",
                param_type="number",
                required=False,
                default=30,
            ),
            TemplateParameter(
                name="refresh_token_expire_days",
                description="Refresh token expiration in days",
                param_type="number",
                required=False,
                default=7,
            ),
        ],
        tags=["auth", "jwt", "security"],
    ),

    # TypeScript Express API Template
    CodeTemplate(
        id="ts-express-api",
        name="Express.js REST API",
        description="A TypeScript Express.js REST API with routes and middleware",
        category=TemplateCategory.REST_API,
        language=TemplateLanguage.TYPESCRIPT,
        template_code='''/**
 * Express.js REST API for {{resource_name}} management.
 */

import express, { Request, Response, NextFunction } from 'express';
import { v4 as uuidv4 } from 'uuid';

const router = express.Router();

interface {{resource_name}} {
  id: string;
  name: string;
  description?: string;
  createdAt: Date;
  updatedAt: Date;
}

interface Create{{resource_name}}Dto {
  name: string;
  description?: string;
}

interface Update{{resource_name}}Dto {
  name?: string;
  description?: string;
}

// In-memory storage (replace with database in production)
const storage = new Map<string, {{resource_name}}>();

// Create
router.post('/', (req: Request, res: Response) => {
  const data: Create{{resource_name}}Dto = req.body;

  if (!data.name) {
    return res.status(400).json({ error: 'Name is required' });
  }

  const now = new Date();
  const item: {{resource_name}} = {
    id: uuidv4(),
    name: data.name,
    description: data.description,
    createdAt: now,
    updatedAt: now,
  };

  storage.set(item.id, item);
  res.status(201).json(item);
});

// List all
router.get('/', (req: Request, res: Response) => {
  const items = Array.from(storage.values());
  res.json(items);
});

// Get by ID
router.get('/:id', (req: Request, res: Response) => {
  const item = storage.get(req.params.id);

  if (!item) {
    return res.status(404).json({ error: '{{resource_name}} not found' });
  }

  res.json(item);
});

// Update
router.patch('/:id', (req: Request, res: Response) => {
  const item = storage.get(req.params.id);

  if (!item) {
    return res.status(404).json({ error: '{{resource_name}} not found' });
  }

  const data: Update{{resource_name}}Dto = req.body;

  if (data.name !== undefined) item.name = data.name;
  if (data.description !== undefined) item.description = data.description;
  item.updatedAt = new Date();

  storage.set(item.id, item);
  res.json(item);
});

// Delete
router.delete('/:id', (req: Request, res: Response) => {
  if (!storage.has(req.params.id)) {
    return res.status(404).json({ error: '{{resource_name}} not found' });
  }

  storage.delete(req.params.id);
  res.status(204).send();
});

export default router;
''',
        parameters=[
            TemplateParameter(
                name="resource_name",
                description="Name of the resource (PascalCase, e.g., 'Product')",
                param_type="string",
                required=True,
                default="Item",
            ),
        ],
        tags=["api", "rest", "express", "typescript", "crud"],
    ),

    # Python Database Model Template
    CodeTemplate(
        id="py-sqlalchemy-model",
        name="SQLAlchemy Model",
        description="SQLAlchemy model with common fields and relationships",
        category=TemplateCategory.DATABASE,
        language=TemplateLanguage.PYTHON,
        template_code='''"""
SQLAlchemy model for {{model_name}}.
"""

from datetime import datetime
from typing import Optional
from sqlalchemy import String, DateTime, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship, DeclarativeBase
import uuid


def generate_uuid() -> str:
    return str(uuid.uuid4())


def utc_now() -> datetime:
    return datetime.utcnow()


class Base(DeclarativeBase):
    pass


class {{model_name}}(Base):
    """{{model_name}} database model."""

    __tablename__ = "{{table_name}}"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=generate_uuid,
    )
    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=utc_now,
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=utc_now,
        onupdate=utc_now,
        nullable=False,
    )

    def __repr__(self) -> str:
        return f"<{{model_name}}(id={self.id}, name={self.name})>"

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
''',
        parameters=[
            TemplateParameter(
                name="model_name",
                description="Name of the model (PascalCase, e.g., 'Product')",
                param_type="string",
                required=True,
                default="Item",
            ),
            TemplateParameter(
                name="table_name",
                description="Database table name (snake_case, e.g., 'products')",
                param_type="string",
                required=True,
                default="items",
            ),
        ],
        tags=["database", "sqlalchemy", "orm", "model"],
    ),

    # Python Unit Test Template
    CodeTemplate(
        id="py-pytest-tests",
        name="Pytest Test Suite",
        description="Pytest test suite with fixtures and common patterns",
        category=TemplateCategory.TESTING,
        language=TemplateLanguage.PYTHON,
        template_code='''"""
Test suite for {{module_name}}.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime


# Fixtures
@pytest.fixture
def sample_data():
    """Provide sample test data."""
    return {
        "id": "test-id-123",
        "name": "Test Item",
        "created_at": datetime.utcnow(),
    }


@pytest.fixture
def mock_{{service_name}}():
    """Provide a mock {{service_name}}."""
    mock = Mock()
    mock.get.return_value = {"id": "1", "name": "Test"}
    mock.list.return_value = [{"id": "1", "name": "Test"}]
    return mock


# Test Classes
class Test{{class_name}}:
    """Tests for {{class_name}}."""

    def test_create_success(self, sample_data):
        """Test successful creation."""
        # Arrange
        data = sample_data

        # Act
        result = self._create_item(data)

        # Assert
        assert result is not None
        assert result["name"] == data["name"]

    def test_create_invalid_input(self):
        """Test creation with invalid input."""
        # Arrange
        invalid_data = {}

        # Act & Assert
        with pytest.raises(ValueError):
            self._create_item(invalid_data)

    def test_get_existing(self, sample_data):
        """Test getting an existing item."""
        # Arrange
        item_id = sample_data["id"]

        # Act
        result = self._get_item(item_id)

        # Assert
        assert result is not None
        assert result["id"] == item_id

    def test_get_not_found(self):
        """Test getting a non-existent item."""
        # Act & Assert
        with pytest.raises(KeyError):
            self._get_item("nonexistent-id")

    def test_list_empty(self):
        """Test listing when empty."""
        # Act
        result = self._list_items()

        # Assert
        assert result == []

    def test_delete_success(self, sample_data):
        """Test successful deletion."""
        # Arrange
        item_id = sample_data["id"]

        # Act
        result = self._delete_item(item_id)

        # Assert
        assert result is True

    # Helper methods (replace with actual implementation)
    def _create_item(self, data):
        if not data.get("name"):
            raise ValueError("Name is required")
        return {"id": "new-id", **data}

    def _get_item(self, item_id):
        if item_id == "nonexistent-id":
            raise KeyError("Item not found")
        return {"id": item_id, "name": "Test"}

    def _list_items(self):
        return []

    def _delete_item(self, item_id):
        return True
''',
        parameters=[
            TemplateParameter(
                name="module_name",
                description="Name of the module being tested",
                param_type="string",
                required=True,
                default="my_module",
            ),
            TemplateParameter(
                name="class_name",
                description="Name of the class being tested (PascalCase)",
                param_type="string",
                required=True,
                default="MyClass",
            ),
            TemplateParameter(
                name="service_name",
                description="Name of the service (snake_case)",
                param_type="string",
                required=False,
                default="service",
            ),
        ],
        tags=["testing", "pytest", "unit-tests"],
    ),

    # JavaScript Utility Functions Template
    CodeTemplate(
        id="js-utility-functions",
        name="JavaScript Utilities",
        description="Common JavaScript utility functions",
        category=TemplateCategory.UTILITY,
        language=TemplateLanguage.JAVASCRIPT,
        template_code='''/**
 * Utility functions for {{module_name}}.
 */

/**
 * Debounce a function call.
 * @param {Function} fn - Function to debounce
 * @param {number} delay - Delay in milliseconds
 * @returns {Function} Debounced function
 */
export function debounce(fn, delay = 300) {
  let timeoutId;
  return function (...args) {
    clearTimeout(timeoutId);
    timeoutId = setTimeout(() => fn.apply(this, args), delay);
  };
}

/**
 * Throttle a function call.
 * @param {Function} fn - Function to throttle
 * @param {number} limit - Minimum time between calls
 * @returns {Function} Throttled function
 */
export function throttle(fn, limit = 300) {
  let inThrottle;
  return function (...args) {
    if (!inThrottle) {
      fn.apply(this, args);
      inThrottle = true;
      setTimeout(() => (inThrottle = false), limit);
    }
  };
}

/**
 * Deep clone an object.
 * @param {any} obj - Object to clone
 * @returns {any} Cloned object
 */
export function deepClone(obj) {
  if (obj === null || typeof obj !== 'object') return obj;
  if (Array.isArray(obj)) return obj.map(deepClone);
  return Object.fromEntries(
    Object.entries(obj).map(([key, value]) => [key, deepClone(value)])
  );
}

/**
 * Check if two objects are deeply equal.
 * @param {any} a - First object
 * @param {any} b - Second object
 * @returns {boolean} True if equal
 */
export function deepEqual(a, b) {
  if (a === b) return true;
  if (typeof a !== typeof b) return false;
  if (typeof a !== 'object' || a === null || b === null) return false;

  const keysA = Object.keys(a);
  const keysB = Object.keys(b);

  if (keysA.length !== keysB.length) return false;

  return keysA.every((key) => deepEqual(a[key], b[key]));
}

/**
 * Generate a unique ID.
 * @returns {string} Unique ID
 */
export function generateId() {
  return `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
}

/**
 * Format a date string.
 * @param {Date|string} date - Date to format
 * @param {string} format - Format string (simple)
 * @returns {string} Formatted date
 */
export function formatDate(date, format = 'YYYY-MM-DD') {
  const d = new Date(date);
  const year = d.getFullYear();
  const month = String(d.getMonth() + 1).padStart(2, '0');
  const day = String(d.getDate()).padStart(2, '0');
  const hours = String(d.getHours()).padStart(2, '0');
  const minutes = String(d.getMinutes()).padStart(2, '0');
  const seconds = String(d.getSeconds()).padStart(2, '0');

  return format
    .replace('YYYY', year)
    .replace('MM', month)
    .replace('DD', day)
    .replace('HH', hours)
    .replace('mm', minutes)
    .replace('ss', seconds);
}

/**
 * Parse query string to object.
 * @param {string} queryString - Query string to parse
 * @returns {Object} Parsed parameters
 */
export function parseQueryString(queryString) {
  if (!queryString || queryString === '?') return {};
  const query = queryString.startsWith('?') ? queryString.slice(1) : queryString;
  return Object.fromEntries(
    query.split('&').map((param) => {
      const [key, value] = param.split('=');
      return [decodeURIComponent(key), decodeURIComponent(value || '')];
    })
  );
}

/**
 * Convert object to query string.
 * @param {Object} params - Parameters to convert
 * @returns {string} Query string
 */
export function toQueryString(params) {
  return Object.entries(params)
    .filter(([, value]) => value !== undefined && value !== null)
    .map(([key, value]) => `${encodeURIComponent(key)}=${encodeURIComponent(value)}`)
    .join('&');
}
''',
        parameters=[
            TemplateParameter(
                name="module_name",
                description="Name of the utility module",
                param_type="string",
                required=False,
                default="common",
            ),
        ],
        tags=["utility", "helpers", "javascript"],
    ),
]


class TemplateService:
    """Service for managing code templates."""

    def __init__(self):
        self._templates: dict[str, CodeTemplate] = {}
        self._load_builtin_templates()

    def _load_builtin_templates(self) -> None:
        """Load built-in templates."""
        for template in BUILTIN_TEMPLATES:
            self._templates[template.id] = template

    def get_template(self, template_id: str) -> Optional[CodeTemplate]:
        """Get a template by ID."""
        return self._templates.get(template_id)

    def list_templates(
        self,
        category: Optional[TemplateCategory] = None,
        language: Optional[TemplateLanguage] = None,
        tags: Optional[list[str]] = None,
    ) -> list[CodeTemplate]:
        """List templates with optional filtering."""
        templates = list(self._templates.values())

        if category:
            templates = [t for t in templates if t.category == category]

        if language:
            templates = [
                t for t in templates
                if t.language == language or t.language == TemplateLanguage.ANY
            ]

        if tags:
            templates = [
                t for t in templates
                if any(tag in t.tags for tag in tags)
            ]

        return sorted(templates, key=lambda t: (-t.usage_count, t.name))

    def create_template(
        self,
        name: str,
        description: str,
        category: TemplateCategory,
        language: TemplateLanguage,
        template_code: str,
        test_template: Optional[str] = None,
        parameters: Optional[list[dict]] = None,
        tags: Optional[list[str]] = None,
        created_by: Optional[str] = None,
    ) -> CodeTemplate:
        """Create a new custom template."""
        template_id = f"custom-{str(uuid.uuid4())[:8]}"

        params = []
        if parameters:
            for p in parameters:
                params.append(TemplateParameter(
                    name=p["name"],
                    description=p.get("description", ""),
                    param_type=p.get("type", "string"),
                    required=p.get("required", True),
                    default=p.get("default"),
                    enum_values=p.get("enum_values"),
                ))

        template = CodeTemplate(
            id=template_id,
            name=name,
            description=description,
            category=category,
            language=language,
            template_code=template_code,
            test_template=test_template,
            parameters=params,
            tags=tags or [],
            is_builtin=False,
            created_by=created_by,
        )

        self._templates[template_id] = template
        return template

    def update_template(
        self,
        template_id: str,
        **updates,
    ) -> Optional[CodeTemplate]:
        """Update a template (custom templates only)."""
        template = self._templates.get(template_id)
        if not template or template.is_builtin:
            return None

        for key, value in updates.items():
            if hasattr(template, key) and value is not None:
                setattr(template, key, value)

        template.updated_at = datetime.utcnow()
        return template

    def delete_template(self, template_id: str) -> bool:
        """Delete a template (custom templates only)."""
        template = self._templates.get(template_id)
        if not template or template.is_builtin:
            return False

        del self._templates[template_id]
        return True

    def render_template(
        self,
        template_id: str,
        params: dict[str, Any],
    ) -> Optional[tuple[str, Optional[str]]]:
        """
        Render a template with parameters.

        Returns tuple of (code, tests) or None if template not found.
        """
        template = self._templates.get(template_id)
        if not template:
            return None

        # Increment usage count
        template.usage_count += 1

        code = template.render(params)
        tests = template.render_tests(params)

        return code, tests

    def get_categories(self) -> list[dict]:
        """Get list of template categories with counts."""
        category_counts: dict[str, int] = {}
        for template in self._templates.values():
            cat = template.category.value
            category_counts[cat] = category_counts.get(cat, 0) + 1

        return [
            {"id": cat.value, "name": cat.name.replace("_", " ").title(), "count": category_counts.get(cat.value, 0)}
            for cat in TemplateCategory
        ]

    def get_languages(self) -> list[dict]:
        """Get list of supported languages with counts."""
        lang_counts: dict[str, int] = {}
        for template in self._templates.values():
            lang = template.language.value
            lang_counts[lang] = lang_counts.get(lang, 0) + 1

        return [
            {"id": lang.value, "name": lang.name.replace("_", " ").title(), "count": lang_counts.get(lang.value, 0)}
            for lang in TemplateLanguage
        ]


# Singleton instance
_template_service: Optional[TemplateService] = None


def get_template_service() -> TemplateService:
    """Get or create the template service singleton."""
    global _template_service
    if _template_service is None:
        _template_service = TemplateService()
    return _template_service
