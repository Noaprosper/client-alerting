# API Endpoint Update - Scaleway Console API

## Date: 2026-09-08

## Problem
The original API endpoint configuration was incorrect. The code was using:
```
https://api.scaleway.com/resource-private/v1alpha1/filtered-counters
```

But testing showed the working endpoint is:
```
https://api.scaleway.com/resource-private/v1alpha1/dashboard
```

## Changes Made

### 1. Configuration Files Updated

#### `.env`
```diff
- CONSOLE_API_URL=https://api.scaleway.com/resource-private/v1alpha1
+ CONSOLE_API_URL=https://api.scaleway.com/resource-private/v1alpha1/dashboard
```

#### `.env.example`
```diff
- CONSOLE_API_URL=https://api.scaleway.com/resource-private/v1alpha1
+ CONSOLE_API_URL=https://api.scaleway.com/resource-private/v1alpha1/dashboard
```

### 2. Code Files Updated

#### `cron-match-incidents/main.py`
- Updated `call_api()` function to use `CONSOLE_API_URL` directly (which now includes `/dashboard`)
- Changed from: `requests.get(f'{CONSOLE_API_URL}/filtered-counters', ...)`
- Changed to: `requests.get(CONSOLE_API_URL, ...)`
- Updated docstring to reflect `/dashboard` endpoint

### 3. Documentation Files Updated

- `README.md` - Updated CONSOLE_API_URL example
- `INSTALL.md` - Updated CONSOLE_API_URL example  
- `QUICKSTART.md` - Updated CONSOLE_API_URL example
- `ARCHITECTURE.md` - Updated endpoint documentation from `/filtered-counters` to `/dashboard`

### 4. New Files Created

#### `cron-match-incidents/test_api.py`
Test script to verify API connectivity and configuration.

Usage:
```bash
cd cron-match-incidents
source venv/bin/activate
python test_api.py [ORG_ID]
```

#### `dashboard/.env.local.example`
Example environment file for dashboard configuration.

## API Endpoint Details

### Endpoint
```
GET /resource-private/v1alpha1/dashboard
```

### Parameters
- `organization_id` (UUID, required) - The organization to query
- `products` (int[], required) - Resource types to count (from ResourceCount.Type enum)
- `localities` (int, required) - Locality filter (use 1 for all zones)
- `strategy` (int, optional) - Data source strategy (1=mixed)

### Example Request
```bash
curl -H "X-Auth-Token: scw_xxx" \
  "https://api.scaleway.com/resource-private/v1alpha1/dashboard?organization_id=11111111-1111-1111-1111-111111111111&products=1&products=3&localities=1&strategy=1"
```

### Response Format
```json
{
  "counters": [
    {
      "type": 1,
      "values": {"fr-par-1": 5, "fr-par-2": 3},
      "unit": 0
    },
    {
      "type": 3,
      "values": {"fr-par-1": 10},
      "unit": 0
    }
  ]
}
```

## Testing

### Test the API Configuration
```bash
cd /Users/cbenard/Desktop/Alert-client/cron-match-incidents
python test_api.py YOUR_ORG_ID
```

### Test the Full Cron Job
```bash
cd /Users/cbenard/Desktop/Alert-client/cron-match-incidents
source venv/bin/activate
python main.py
```

## Required Permissions

The API key must have **READ-ONLY** permissions on:
- `resource_private.v1alpha1.ConsoleApi` - `get` action
- `organizations` - `read` action

**Do NOT grant**: write, delete, create, or update permissions.

## Troubleshooting

### 403 Permission Denied
- Verify API key has read permissions on the target organization
- Check the organization_id is correct
- Ensure API key is not expired

### 404 Not Found
- Verify CONSOLE_API_URL includes `/dashboard` path
- Check that the API endpoint is accessible from your network

### 401 Authentication Failed
- Verify SCALEWAY_API_KEY format (should start with `scw_`)
- Check API key is active and not revoked

## Files Modified Summary

| File | Change |
|------|--------|
| `.env` | Updated CONSOLE_API_URL |
| `.env.example` | Updated CONSOLE_API_URL |
| `cron-match-incidents/main.py` | Updated API call and docstring |
| `cron-match-incidents/test_api.py` | **NEW** - Test script |
| `dashboard/.env.local.example` | **NEW** - Dashboard env example |
| `README.md` | Updated documentation |
| `INSTALL.md` | Updated documentation |
| `QUICKSTART.md` | Updated documentation |
| `ARCHITECTURE.md` | Updated endpoint documentation |

## Next Steps

1. ✅ Configuration updated
2. [ ] Test with real API key and organization_id
3. [ ] Import organizations: `python database/import_csv.py organizations.csv`
4. [ ] Run cron job: `python cron-match-incidents/main.py`
5. [ ] Start dashboard: `cd dashboard && npm run dev`