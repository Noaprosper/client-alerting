# 🧪 Testing Guide - Alert Client Dashboard

## Quick Test Commands

### 1. Validate Configuration
```bash
cd /Users/cbenard/Desktop/Alert-client
python3 validate_config.py
```

Expected output: All checks should be ✅

### 2. Test Scaleway API Connection
```bash
cd cron-match-incidents
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Test with your organization ID
python test_api.py YOUR_ORG_ID_HERE
```

### 3. Import Organizations
```bash
cd database

# Edit the CSV file with your real organization IDs
nano organizations.csv

# Import into database
python import_csv.py organizations.csv

# Verify import
psql -d alert_client -c "SELECT * FROM organizations;"
```

### 4. Test Cron Job
```bash
cd cron-match-incidents
source venv/bin/activate
python main.py
```

Expected output:
```
INFO - Starting match-incidents
INFO - Fetched X open incidents
INFO - Found X organizations
INFO - Saved X incidents
INFO - Saved X alerts
INFO - Done: X alerts in XXXms
```

### 5. Test Dashboard
```bash
cd dashboard

# Copy and edit env file
cp .env.local.example .env.local
nano .env.local  # Add your DATABASE_URL

# Install and run
npm install
npm run dev

# Open http://localhost:3000
```

## Test Checklist

- [ ] Configuration validation passes (`python3 validate_config.py`)
- [ ] API test succeeds with your organization ID
- [ ] Organizations imported successfully
- [ ] Cron job runs without errors
- [ ] Dashboard loads at http://localhost:3000
- [ ] Alerts are displayed correctly

## Common Issues

### "Permission denied (403)" on API test
**Fix**: Your API key needs READ permissions on the organization
- Go to Scaleway Console → IAM → API Keys
- Edit your API key and add read permissions

### "No organizations found"
**Fix**: Import organizations from CSV
```bash
cd database
python import_csv.py organizations.csv
```

### "DATABASE_URL not set"
**Fix**: Create .env file in cron-match-incidents/
```bash
cp ../.env.example .env
nano .env  # Fill in your values
```

### Dashboard won't start
**Fix**: Install dependencies and set DATABASE_URL
```bash
cd dashboard
npm install
cp .env.local.example .env.local
nano .env.local  # Add DATABASE_URL
npm run dev
```

## API Endpoint Details

### Current Configuration
- **Endpoint**: `https://api.scaleway.com/resource-private/v1alpha1/dashboard`
- **Method**: GET
- **Auth**: X-Auth-Token header
- **Params**: organization_id, products, localities, strategy

### Test with curl
```bash
curl -H "X-Auth-Token: scw_xxx" \
  "https://api.scaleway.com/resource-private/v1alpha1/dashboard?organization_id=YOUR_ORG_ID&products=1&localities=1&strategy=1"
```

Expected response:
```json
{
  "counters": [
    {
      "type": 1,
      "values": {"fr-par-1": 5},
      "unit": 0
    }
  ]
}
```

## Logs Location

- **Cron job**: Console output + `sync_logs` table in database
- **Dashboard**: Browser console + Next.js terminal output
- **Database**: PostgreSQL logs (check your PostgreSQL configuration)

## Support

If you encounter issues:
1. Check the validation: `python3 validate_config.py`
2. Review logs for error messages
3. Verify API key permissions in Scaleway Console
4. Check database connection: `psql -d alert_client -c "\dt"`