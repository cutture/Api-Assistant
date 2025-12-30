# RESTful API Design Guide

## Introduction

RESTful APIs are the backbone of modern web services. This guide covers essential concepts and best practices for designing robust REST APIs.

## Core Principles

### Resource-Oriented Design

Every entity in your system should be represented as a resource with a unique URL:

- **Users**: `/api/users/{id}`
- **Products**: `/api/products/{id}`
- **Orders**: `/api/orders/{id}`

### HTTP Methods

Use standard HTTP methods appropriately:

| Method | Purpose | Idempotent |
|--------|---------|------------|
| GET | Retrieve resources | Yes |
| POST | Create new resources | No |
| PUT | Update entire resource | Yes |
| PATCH | Partial update | No |
| DELETE | Remove resource | Yes |

## Status Codes

Return meaningful HTTP status codes:

- **200 OK**: Successful GET, PUT, PATCH, or DELETE
- **201 Created**: Successful POST
- **400 Bad Request**: Invalid request data
- **401 Unauthorized**: Authentication required
- **404 Not Found**: Resource doesn't exist
- **500 Internal Server Error**: Server-side error

## Versioning

Always version your API:

```
https://api.example.com/v1/users
https://api.example.com/v2/users
```

## Example Request

```bash
curl -X GET https://api.example.com/v1/users/123 \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json"
```

## Response Format

```json
{
  "data": {
    "id": 123,
    "name": "John Doe",
    "email": "john@example.com"
  },
  "meta": {
    "timestamp": "2025-12-30T00:00:00Z"
  }
}
```

## Error Handling

Provide clear error messages:

```json
{
  "error": {
    "code": "RESOURCE_NOT_FOUND",
    "message": "The requested user was not found",
    "details": {
      "user_id": 123
    }
  }
}
```

## Pagination

For large collections, implement pagination:

```
GET /api/users?page=2&limit=50
```

Response should include pagination metadata:

```json
{
  "data": [...],
  "pagination": {
    "page": 2,
    "limit": 50,
    "total": 500,
    "pages": 10
  }
}
```

## Security

1. Always use HTTPS
2. Implement rate limiting
3. Validate all inputs
4. Use secure authentication (OAuth 2.0)
5. Never expose sensitive data

## Conclusion

Following these REST API design principles will help you create maintainable, scalable, and developer-friendly APIs.
