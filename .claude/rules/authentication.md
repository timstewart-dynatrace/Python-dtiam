# Authentication

This document defines authentication methods and credential management for dtiam.

## Authentication Methods

### OAuth2 (Recommended)

OAuth2 client credentials flow with automatic token refresh.

**Best for:**
- Automation and CI/CD
- Long-running processes
- Production deployments

**Setup:**
```bash
export DTIAM_CLIENT_SECRET=dt0s01.CLIENTID.SECRET
export DTIAM_ACCOUNT_UUID=your-account-uuid
```

**Features:**
- Auto-refreshes tokens before expiration
- Supports custom scopes
- Logs token refresh events (verbose mode)

### Static Bearer Token

Pre-generated bearer token without refresh capability.

**Best for:**
- Quick testing
- Debugging
- One-off operations

**Setup:**
```bash
export DTIAM_BEARER_TOKEN=your-token
export DTIAM_ACCOUNT_UUID=your-account-uuid
```

**Limitations:**
- Does NOT auto-refresh
- Fails when token expires
- Warning displayed when used

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `DTIAM_CLIENT_SECRET` | OAuth2 client secret | For OAuth2 |
| `DTIAM_CLIENT_ID` | OAuth2 client ID | Optional (auto-extracted) |
| `DTIAM_ACCOUNT_UUID` | Dynatrace account UUID | Yes |
| `DTIAM_BEARER_TOKEN` | Static bearer token | For bearer auth |
| `DTIAM_API_URL` | Custom IAM API base URL | No |
| `DTIAM_CONTEXT` | Override current context | No |
| `DTIAM_ENVIRONMENT_URL` | Environment URL for apps | No |

### Client ID Auto-Extraction

`DTIAM_CLIENT_ID` is optional. When not set, it's extracted from `DTIAM_CLIENT_SECRET`:

```
Secret format: dt0s01.CLIENTID.SECRETPART
Auto-extracted: CLIENTID
```

## OAuth2 Scopes

### Default Scopes

The client requests these scopes by default:

```
account-idm-read
account-idm-write
account-env-read
account-env-write
account-uac-read
account-uac-write
iam-policies-management
iam:users:read
iam:groups:read
iam:policies:read
iam:policies:write
iam:bindings:read
iam:bindings:write
iam:boundaries:read
iam:boundaries:write
iam:effective-permissions:read
```

### Custom Scopes

Specify custom scopes in credentials:

```yaml
credentials:
  - name: limited-access
    credential:
      client-id: dt0s01.XXX
      client-secret: dt0s01.XXX.YYY
      scopes: account-idm-read iam:users:read
```

Or via CLI:

```bash
dtiam config set-credentials NAME \
  --client-secret dt0s01.XXX.YYY \
  --scopes "account-idm-read iam:users:read"
```

### Scope Validation

On token retrieval, granted scopes are compared to requested:

```python
if missing_scopes:
    logger.warning(
        f"Some requested scopes were not granted: {' '.join(sorted(missing_scopes))}"
    )
```

### Common Scope Requirements

| Operation | Required Scopes |
|-----------|-----------------|
| Read groups | `account-idm-read`, `iam:groups:read` |
| Manage policies | `iam-policies-management`, `iam:policies:write` |
| Read users | `account-idm-read`, `iam:users:read` |
| Effective permissions | `iam:effective-permissions:read` |
| App Engine apps | `app-engine:apps:run` |

## Token Management

### Token Flow

1. Client checks if token is expired (or will expire in 30 seconds)
2. If expired, requests new token from OAuth2 endpoint
3. Token is cached in memory for duration
4. Authorization header is added to all requests

### Token Endpoint

```
POST https://sso.dynatrace.com/sso/oauth2/token
Content-Type: application/x-www-form-urlencoded

grant_type=client_credentials
client_id={client_id}
client_secret={client_secret}
scope={requested_scopes}
```

### Token Response

```json
{
  "access_token": "dt0c01.XXX.YYY",
  "token_type": "Bearer",
  "expires_in": 300,
  "scope": "account-idm-read iam:users:read"
}
```

## Credential Storage

### Config File Location

XDG-compliant: `~/.config/dtiam/config`

### Credential Entry Structure

```yaml
credentials:
  - name: prod-creds
    credential:
      client-id: dt0s01.XXX
      client-secret: dt0s01.XXX.YYY
      environment-url: https://abc123.live.dynatrace.com
      api-url: https://api.dynatrace.com/iam/v1
      scopes: account-idm-read iam:users:read
```

### Fields

| Field | Description | Required |
|-------|-------------|----------|
| `client-id` | OAuth2 client ID | No (auto-extracted) |
| `client-secret` | OAuth2 client secret | Yes |
| `environment-url` | Dynatrace environment URL | No |
| `api-url` | Custom IAM API base URL | No |
| `scopes` | Custom OAuth2 scopes (space-separated) | No |

## Security Best Practices

### Never Log Secrets

```python
# WRONG
logger.info(f"Using secret: {client_secret}")

# CORRECT
from dtiam.config import mask_secret
logger.info(f"Using secret: {mask_secret(client_secret)}")
```

### File Permissions

Config file should have restricted permissions:
```bash
chmod 600 ~/.config/dtiam/config
```

### Environment Over Arguments

Never accept secrets as CLI arguments:
```bash
# WRONG - appears in shell history
dtiam --secret dt0s01.XXX.YYY get groups

# CORRECT - use environment variable
export DTIAM_CLIENT_SECRET=dt0s01.XXX.YYY
dtiam get groups
```

## Debugging Authentication

### Verbose Mode

```bash
dtiam -v get groups
```

Shows:
- Token retrieval attempts
- Token refresh events
- Granted vs requested scopes
- API request details

### Common Issues

**"401 Unauthorized"**
- Token expired (for bearer tokens)
- Invalid credentials
- Check `DTIAM_CLIENT_SECRET` format

**"403 Forbidden"**
- Missing required scopes
- OAuth client not configured with permissions
- Check scopes in Dynatrace console

**"No context configured"**
- No credentials set up
- Run `dtiam config set-credentials`
