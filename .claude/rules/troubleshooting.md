# Troubleshooting

This document covers common issues and solutions for dtiam.

## Authentication Errors

### "No context configured"

**Cause:** No credentials or context set up.

**Solution:**
```bash
# Set up credentials
dtiam config set-credentials mycontext \
  --client-secret dt0s01.CLIENTID.SECRET \
  --account-uuid your-account-uuid

# Use the context
dtiam config use-context mycontext

# Verify
dtiam config current-context
```

### "401 Unauthorized"

**Causes:**
- Invalid credentials
- Expired bearer token
- Malformed client secret

**Solutions:**

1. Verify client secret format:
   ```
   Correct: dt0s01.CLIENTID.SECRETPART
   ```

2. Check environment variable:
   ```bash
   echo $DTIAM_CLIENT_SECRET
   ```

3. For bearer tokens, regenerate (they expire):
   ```bash
   # Bearer tokens cannot be refreshed
   # Use OAuth2 instead for long-running operations
   ```

4. Test with verbose mode:
   ```bash
   dtiam -v get groups
   ```

### "403 Forbidden"

**Causes:**
- Missing OAuth2 scopes
- OAuth client not configured with required permissions
- Account-level permission restrictions

**Solutions:**

1. Check required scopes for operation:
   | Operation | Required Scopes |
   |-----------|-----------------|
   | Read groups/users | `account-idm-read`, `iam:groups:read` |
   | Manage policies | `iam-policies-management` |
   | Effective permissions | `iam:effective-permissions:read` |

2. Verify OAuth client configuration in Dynatrace console

3. Use verbose mode to see granted scopes:
   ```bash
   dtiam -v get groups
   # Look for: "Granted scopes: ..."
   ```

4. Add custom scopes if needed:
   ```bash
   dtiam config set-credentials NAME \
     --client-secret dt0s01.XXX.YYY \
     --scopes "account-idm-read iam:groups:read iam-policies-management"
   ```

### "Token refresh failed"

**Cause:** OAuth2 token could not be refreshed.

**Solutions:**

1. Verify client secret is still valid
2. Check network connectivity to `sso.dynatrace.com`
3. Verify OAuth client hasn't been disabled

## Connection Errors

### "Connection refused" / "Network unreachable"

**Solutions:**

1. Check internet connectivity
2. Verify firewall allows HTTPS to:
   - `api.dynatrace.com`
   - `sso.dynatrace.com`
   - `*.apps.dynatrace.com` (for App Engine)

3. Check proxy settings:
   ```bash
   echo $HTTPS_PROXY
   echo $HTTP_PROXY
   ```

### "SSL certificate error"

**Solutions:**

1. Ensure system time is correct
2. Update CA certificates
3. Check for corporate SSL inspection (may need custom CA)

## Import Errors

### "ModuleNotFoundError: No module named 'dtiam'"

**Cause:** Package not installed or not in development mode.

**Solution:**
```bash
# Install in development mode
pip install -e .

# Or install from PyPI (when available)
pip install dtiam
```

### "ImportError: cannot import name 'X'"

**Causes:**
- Wrong Python version
- Outdated installation
- Renamed module

**Solutions:**

1. Check Python version (requires 3.9+):
   ```bash
   python --version
   ```

2. Reinstall:
   ```bash
   pip uninstall dtiam
   pip install -e .
   ```

## Resource Not Found

### "Resource 'xxx' not found"

**Causes:**
- Resource doesn't exist
- Wrong identifier (name vs UUID)
- Resource is in different level/scope

**Solutions:**

1. List resources first:
   ```bash
   dtiam get groups
   dtiam get policies --level account
   ```

2. Try name-based lookup:
   ```bash
   dtiam describe group "My Group Name"
   ```

3. For policies/bindings, specify correct level:
   ```bash
   dtiam get policies --level environment --level-id abc12345
   ```

### "404 Not Found" from API

**Note:** This is often normal. Many Dynatrace API endpoints don't support direct GET by ID.
The CLI handles this by falling back to list filtering.

If you see 404 errors in verbose mode but the command succeeds, this is expected behavior.

## Output Issues

### Truncated output / Missing columns

**Solutions:**

1. Use wide output:
   ```bash
   dtiam get groups -o wide
   ```

2. Use JSON/YAML for complete data:
   ```bash
   dtiam get groups -o json
   dtiam describe group "My Group" -o yaml
   ```

3. Adjust terminal width

### "UnicodeEncodeError"

**Cause:** Terminal doesn't support Unicode.

**Solution:**
```bash
# Use plain mode
dtiam --plain get groups

# Or set encoding
export PYTHONIOENCODING=utf-8
```

## Performance Issues

### Slow response times

**Solutions:**

1. API rate limiting - wait and retry
2. Large result sets - use filtering:
   ```bash
   dtiam get groups --name "Team"
   ```

3. Check verbose output for retry messages:
   ```bash
   dtiam -v get groups
   ```

### High memory usage

**Cause:** Very large result sets.

**Solution:** Filter results:
```bash
dtiam get users --email "@company.com"
```

## Configuration Issues

### Config file not found

**Solution:** Create initial config:
```bash
dtiam config set-credentials default \
  --client-secret dt0s01.XXX.YYY \
  --account-uuid your-uuid
```

### Config file permission errors

**Solution:**
```bash
chmod 600 ~/.config/dtiam/config
```

### YAML parsing errors

**Cause:** Invalid YAML in config file.

**Solution:**
1. Validate YAML syntax
2. Check for tabs (use spaces)
3. Regenerate config:
   ```bash
   # Backup existing
   mv ~/.config/dtiam/config ~/.config/dtiam/config.bak

   # Create new
   dtiam config set-credentials ...
   ```

## Bulk Operation Issues

### "Dry run mode - no changes made"

**Note:** Dry run is enabled by default for safety.

**Solution:**
```bash
# Execute for real
dtiam bulk create-groups-with-policies --file data.csv --no-dry-run
```

### CSV parsing errors

**Solutions:**

1. Check CSV format:
   ```csv
   group_name,policy_name,level,level_id,management_zones,boundary_name,description
   ```

2. Ensure proper quoting for values with commas
3. Use UTF-8 encoding without BOM

## Debug Mode

### Enable full debugging

```bash
# Verbose mode
dtiam -v get groups

# See HTTP requests
dtiam -v -v get groups 2>&1 | grep -E "(GET|POST|PUT|DELETE)"
```

### Check version

```bash
dtiam --version
```

### Test connectivity

```bash
# Test OAuth2
curl -s -o /dev/null -w "%{http_code}" \
  https://sso.dynatrace.com/sso/oauth2/token

# Test API
curl -s -o /dev/null -w "%{http_code}" \
  -H "Authorization: Bearer $DTIAM_BEARER_TOKEN" \
  https://api.dynatrace.com/iam/v1/accounts/$DTIAM_ACCOUNT_UUID/groups
```

## Getting Help

1. **Check documentation:**
   - [docs/COMMANDS.md](../../docs/COMMANDS.md) - Command reference
   - [docs/QUICK_START.md](../../docs/QUICK_START.md) - Getting started

2. **Use command help:**
   ```bash
   dtiam --help
   dtiam get --help
   dtiam get groups --help
   ```

3. **Report issues:**
   - GitHub Issues: Include version, command, and error message
   - Enable verbose mode for detailed logs
