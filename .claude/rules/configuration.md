# Configuration

This document defines the configuration file format and management for dtiam.

## Config File Location

XDG Base Directory compliant:
```
~/.config/dtiam/config
```

On Windows:
```
%APPDATA%\dtiam\config
```

## Config Structure

```yaml
api-version: v1
kind: Config
current-context: production
contexts:
  - name: production
    context:
      account-uuid: abc-123-def-456
      credentials-ref: prod-creds
  - name: staging
    context:
      account-uuid: xyz-789-uvw-012
      credentials-ref: staging-creds
credentials:
  - name: prod-creds
    credential:
      client-id: dt0s01.PRODCLIENTID
      client-secret: dt0s01.PRODCLIENTID.SECRETPART
      environment-url: https://abc123.live.dynatrace.com
      api-url: https://api.dynatrace.com/iam/v1
      scopes: account-idm-read iam:users:read
  - name: staging-creds
    credential:
      client-id: dt0s01.STAGINGCLIENTID
      client-secret: dt0s01.STAGINGCLIENTID.SECRETPART
```

## Fields

### Top-Level Fields

| Field | Type | Description |
|-------|------|-------------|
| `api-version` | string | Config format version (`v1`) |
| `kind` | string | Always `Config` |
| `current-context` | string | Name of active context |
| `contexts` | list | Context definitions |
| `credentials` | list | Credential definitions |

### Context Fields

| Field | Type | Description |
|-------|------|-------------|
| `name` | string | Context identifier |
| `context.account-uuid` | string | Dynatrace account UUID |
| `context.credentials-ref` | string | Reference to credentials entry |

### Credential Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | Yes | Credential identifier |
| `credential.client-id` | string | No | OAuth2 client ID (auto-extracted if not set) |
| `credential.client-secret` | string | Yes | OAuth2 client secret |
| `credential.environment-url` | string | No | Dynatrace environment URL |
| `credential.api-url` | string | No | Custom IAM API base URL |
| `credential.scopes` | string | No | Custom OAuth2 scopes (space-separated) |

## Config Commands

### Set Credentials

```bash
# Basic setup
dtiam config set-credentials prod \
  --client-secret dt0s01.CLIENTID.SECRET \
  --account-uuid abc-123-def-456

# With custom scopes
dtiam config set-credentials limited \
  --client-secret dt0s01.CLIENTID.SECRET \
  --account-uuid abc-123-def-456 \
  --scopes "account-idm-read iam:users:read"

# With environment URL
dtiam config set-credentials prod \
  --client-secret dt0s01.CLIENTID.SECRET \
  --account-uuid abc-123-def-456 \
  --environment-url https://abc123.live.dynatrace.com
```

### Manage Contexts

```bash
# Create/update context
dtiam config set-context production \
  --account-uuid abc-123-def-456 \
  --credentials-ref prod

# Switch context
dtiam config use-context production

# View current context
dtiam config current-context

# List all contexts
dtiam config get-contexts
```

### View Configuration

```bash
# Show full config
dtiam config view

# Show specific context
dtiam config get-contexts --name production
```

## Environment Variable Overrides

Environment variables take precedence over config file:

| Variable | Overrides |
|----------|-----------|
| `DTIAM_CONTEXT` | `current-context` |
| `DTIAM_CLIENT_ID` | `credential.client-id` |
| `DTIAM_CLIENT_SECRET` | `credential.client-secret` |
| `DTIAM_ACCOUNT_UUID` | `context.account-uuid` |
| `DTIAM_API_URL` | `credential.api-url` |
| `DTIAM_ENVIRONMENT_URL` | `credential.environment-url` |
| `DTIAM_BEARER_TOKEN` | Uses bearer auth instead of OAuth2 |

### Override Priority

1. Environment variables (highest)
2. CLI flags (`--context`)
3. Config file `current-context`

## Multi-Account Setup

Example for managing multiple accounts:

```yaml
api-version: v1
kind: Config
current-context: production
contexts:
  - name: production
    context:
      account-uuid: prod-account-uuid
      credentials-ref: prod-creds
  - name: staging
    context:
      account-uuid: staging-account-uuid
      credentials-ref: staging-creds
  - name: development
    context:
      account-uuid: dev-account-uuid
      credentials-ref: dev-creds
credentials:
  - name: prod-creds
    credential:
      client-secret: dt0s01.PRODID.PRODSECRET
  - name: staging-creds
    credential:
      client-secret: dt0s01.STAGEID.STAGESECRET
  - name: dev-creds
    credential:
      client-secret: dt0s01.DEVID.DEVSECRET
```

Usage:
```bash
# Switch between accounts
dtiam config use-context production
dtiam get groups

dtiam config use-context staging
dtiam get groups

# One-off context override
dtiam --context development get groups
```

## Filtering Resources

All `get` commands support client-side filtering:

### Filter Options

| Command | Option | Description |
|---------|--------|-------------|
| `get groups` | `--name` | Filter by group name |
| `get users` | `--email` | Filter by email |
| `get policies` | `--name` | Filter by policy name |
| `get boundaries` | `--name` | Filter by boundary name |
| `get environments` | `--name` | Filter by environment name |
| `get service-users` | `--name` | Filter by service user name |
| `get apps` | `--name` | Filter by app name |
| `get schemas` | `--name` | Filter by schema ID |

### Filter Behavior

- **Case-insensitive:** `--name prod` matches "Production"
- **Substring match:** `--name LOB` matches "LOB5", "MyLOBTeam"
- **Client-side:** Full list fetched, then filtered locally

### Implementation Pattern

```python
results = handler.list()
if name:
    results = [r for r in results if name.lower() in r.get("name", "").lower()]
```

## Output Formats

Control output with `-o` / `--output`:

| Format | Description |
|--------|-------------|
| `table` | Human-readable table (default) |
| `json` | JSON format |
| `yaml` | YAML format |
| `csv` | CSV format |
| `wide` | Extended table with more columns |

Examples:
```bash
dtiam get groups -o json
dtiam get policies -o yaml
dtiam get users -o csv > users.csv
```

## Global Options

Available on all commands:

| Option | Short | Description |
|--------|-------|-------------|
| `--context` | `-c` | Override context |
| `--output` | `-o` | Output format |
| `--verbose` | `-v` | Verbose mode |
| `--plain` | | No colors |
| `--dry-run` | | Preview without changes |

## Pydantic Models

Configuration is validated using Pydantic:

```python
from dtiam.config import Config, load_config

# Load and validate config
config = load_config()

# Access typed fields
account_uuid = config.contexts[0].context.account_uuid
```

### Model Hierarchy

```
Config
├── api_version: str
├── kind: str
├── current_context: str
├── contexts: list[ContextEntry]
│   └── ContextEntry
│       ├── name: str
│       └── context: Context
│           ├── account_uuid: str
│           └── credentials_ref: str
└── credentials: list[CredentialEntry]
    └── CredentialEntry
        ├── name: str
        └── credential: Credential
            ├── client_id: str | None
            ├── client_secret: str
            ├── environment_url: str | None
            ├── api_url: str | None
            └── scopes: str | None
```
