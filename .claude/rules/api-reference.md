# API Reference

This document defines the Dynatrace IAM API endpoints and patterns used by dtiam.

## Base URLs

### IAM API

```
https://api.dynatrace.com/iam/v1/accounts/{account_uuid}
```

### Resolution API (Effective Permissions)

```
https://api.dynatrace.com/iam/v1/resolution/{level_type}/{level_id}/effectivepermissions
```

### Subscription API

```
https://api.dynatrace.com/sub/v2/accounts/{account_uuid}
```

### App Engine Registry API

```
https://{environment-id}.apps.dynatrace.com/platform/app-engine/registry/v1
```

## Resource Endpoints

### Account-Level Resources

| Resource | Path | ID Field |
|----------|------|----------|
| Groups | `/groups` | `uuid` |
| Users | `/users` | `uid` |
| Service Users | `/service-users` | `uid` |
| Platform Tokens | `/platform-tokens` | `id` |
| Limits | `/limits` | N/A |
| Environments | `/environments` | `id` |

### Scoped Resources (Level-Based)

These resources exist at different levels: `account`, `environment`, or `global`.

| Resource | Path Pattern | ID Field |
|----------|--------------|----------|
| Policies | `/repo/{level}/{level_id}/policies` | `uuid` |
| Bindings | `/repo/{level}/{level_id}/bindings` | `policyUuid` + `groupUuid` |
| Boundaries | `/repo/account/{account_uuid}/boundaries` | `uuid` |

**Note:** Boundaries are always at account level, but policies and bindings can be at any level.

### Level Types

| Level | Description | Example Level ID |
|-------|-------------|------------------|
| `account` | Account-wide scope | Account UUID |
| `environment` | Environment-specific | Environment ID (e.g., `abc12345`) |
| `global` | Dynatrace-managed | `global` |

### Example: Policy at Environment Level

```python
# API path for environment-level policy
path = f"/repo/environment/{environment_id}/policies"
```

## App Engine Registry Endpoints

| Resource | Path | ID Field |
|----------|------|----------|
| Apps | `/apps` | `id` |
| App Details | `/apps/{id}` | `id` |

**Authentication:** Uses same OAuth2 token as IAM API with `app-engine:apps:run` scope.

## Subscription Endpoints

| Resource | Path |
|----------|------|
| Subscriptions | `/subscriptions` |
| Forecast | `/subscriptions/forecast` |

## Common Response Patterns

### List Response

Most list endpoints return:

```json
{
  "items": [
    { "uuid": "...", "name": "..." },
    ...
  ]
}
```

**Exception:** Some endpoints return the array directly without wrapper.

### Error Response

```json
{
  "error": {
    "code": 403,
    "message": "Permission denied"
  }
}
```

## Rate Limiting

The API implements rate limiting. The client handles this with:

- Automatic retry with exponential backoff
- Configurable retry counts and delays
- 429 status code detection

## Pagination

Effective permissions endpoint supports pagination:

| Parameter | Description | Default |
|-----------|-------------|---------|
| `page` | Page number | 1 |
| `size` | Page size | 100 |
| `services` | Service filter | (all) |

## Query Parameters

### Effective Permissions

```
GET /resolution/{level}/{id}/effectivepermissions?entityId={uuid}&entityType={type}
```

| Parameter | Required | Values |
|-----------|----------|--------|
| `entityId` | Yes | User UID or Group UUID |
| `entityType` | Yes | `user` or `group` |

## HTTP Methods

| Method | Usage |
|--------|-------|
| `GET` | Retrieve resources |
| `POST` | Create resources |
| `PUT` | Update/replace resources |
| `DELETE` | Delete resources |

## Response Codes

| Code | Meaning |
|------|---------|
| 200 | Success |
| 201 | Created |
| 204 | No Content (successful delete) |
| 400 | Bad Request |
| 401 | Unauthorized |
| 403 | Forbidden |
| 404 | Not Found |
| 429 | Rate Limited |
| 500 | Server Error |

## API Quirks

### 404 Fallback Pattern

Some endpoints don't support direct GET by ID (e.g., `/groups/{uuid}`).
Handlers implement fallback logic:

```python
try:
    response = self.client.get(f"{self.api_path}/{resource_id}")
    return response.json()
except APIError as e:
    if e.status_code == 404:
        # Fall back to filtering the list
        items = self.list()
        for item in items:
            if item.get(self.id_field) == resource_id:
                return item
        return {}
    raise
```

### Binding Identifiers

Bindings use composite keys (policy UUID + group UUID), not single identifiers.

### User Email Lookup

Users can be looked up by email via the list endpoint filter, not direct GET.
