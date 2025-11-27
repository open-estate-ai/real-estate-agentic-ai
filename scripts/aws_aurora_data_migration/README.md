# Aurora Database Migration

Run SQL migrations against Aurora Serverless using RDS Data API.

## Prerequisites

- AWS credentials configured
- Python 3.x
- Aurora cluster running in AWS

## Setup

```bash
# Create virtual environment
python3 -m venv .venv

# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install boto3
```

## Configuration

The script uses these defaults (can be changed in the script):

```
AWS_REGION:         us-east-1
AURORA_CLUSTER_ARN: arn:aws:rds:us-east-1:756375699536:cluster:dev-open-estate-ai-cluster
DB_NAME:            real_estate_agents
DB_USERNAME:        adminuser
SSM_PASSWORD_PARAM: /dev/dev-open-estate-ai/db/password
```

## Usage

### Run default migration (001_init.sql)

```bash
python run_migration.py
```

### Run specific migration file

```bash
python run_migration.py /path/to/migration.sql
```

## What it does

1. Reads SQL file and splits into individual statements
2. Fetches database password from SSM Parameter Store
3. Creates temporary secret in Secrets Manager
4. Executes each SQL statement via RDS Data API
5. Skips statements if objects already exist
6. Deletes temporary secret after completion

## Output

```
📄 Reading migration file
📊 Found X SQL statements to execute

▶️  Executing statement 1/X...
   ✅ Statement executed successfully

============================================================
📊 Migration Results
============================================================
Total statements:     9
✅ Successful:        7
⚠️  Skipped:          2
❌ Failed:            0

✅ Migration completed successfully
```

## Notes

- Script automatically handles "already exists" errors
- Temporary secrets are always cleaned up
- Migration stops on real errors (not on "already exists")
- Safe to run multiple times (idempotent)
