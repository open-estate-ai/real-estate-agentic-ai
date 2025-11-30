import boto3
import uuid
import json

# -----------------------------
# Configuration
# -----------------------------
AWS_REGION = "us-east-1"
AURORA_CLUSTER_ARN = "arn:aws:rds:us-east-1:756375699536:cluster:dev-open-estate-ai-cluster"
DB_NAME = "real_estate_agents"
DB_USERNAME = "adminuser"
# SecureString parameter name
SSM_PASSWORD_PARAM = "/dev/dev-open-estate-ai/db/password"

# Prefix for temporary secrets (name will have a random suffix)
TEMP_SECRET_NAME_PREFIX = "tmp/open-estate-ai/aurora/postgres-cred"

# -----------------------------
# Fetch password from SSM
# -----------------------------


def get_db_password() -> str:
    ssm = boto3.client("ssm", region_name=AWS_REGION)
    resp = ssm.get_parameter(
        Name=SSM_PASSWORD_PARAM,
        WithDecryption=True,
    )
    return resp["Parameter"]["Value"]


def create_temp_secret(password: str) -> str:
    """
    Create a temporary Secrets Manager secret with username/password.
    Returns the secret ARN.
    """
    sm = boto3.client("secretsmanager", region_name=AWS_REGION)

    secret_name = f"{TEMP_SECRET_NAME_PREFIX}-{uuid.uuid4()}"
    secret_string = json.dumps(
        {
            "username": DB_USERNAME,
            "password": password,
        }
    )

    created = sm.create_secret(
        Name=secret_name,
        SecretString=secret_string,
    )
    return created["ARN"]


def delete_secret(secret_arn: str) -> None:
    """Delete the secret immediately (no recovery window)."""
    sm = boto3.client("secretsmanager", region_name=AWS_REGION)
    try:
        sm.delete_secret(
            SecretId=secret_arn,
            ForceDeleteWithoutRecovery=True,
        )
    except sm.exceptions.ResourceNotFoundException:
        # Already deleted or never created successfully
        pass

# -----------------------------
# Execute SQL using Data API
# -----------------------------


def run_query(sql: str, parameters=None):
    if parameters is None:
        parameters = []

    client = boto3.client("rds-data", region_name=AWS_REGION)
    db_password = get_db_password()
    secret_arn = create_temp_secret(db_password)

    try:
        response = client.execute_statement(
            resourceArn=AURORA_CLUSTER_ARN,
            secretArn=secret_arn,
            database=DB_NAME,
            sql=sql,
            parameters=parameters,
            includeResultMetadata=True,
        )
        return response
    finally:
        delete_secret(secret_arn)


# -----------------------------
# Execute SQL migration file
# -----------------------------

def run_migration(sql_file_path: str):
    """
    Execute SQL migration file using Data API.
    Splits SQL into individual statements and executes them.
    """
    import os

    if not os.path.exists(sql_file_path):
        raise FileNotFoundError(f"Migration file not found: {sql_file_path}")

    print(f"📄 Reading migration file: {sql_file_path}")
    with open(sql_file_path, 'r') as f:
        sql_content = f.read()

    # Split SQL into individual statements
    statements = []
    current_stmt = []

    for line in sql_content.split('\n'):
        # Skip comments and empty lines
        stripped = line.strip()
        if not stripped or stripped.startswith('--'):
            continue

        current_stmt.append(line)

        # Check if statement ends with semicolon
        if stripped.endswith(';'):
            stmt = '\n'.join(current_stmt)
            if stmt.strip():
                statements.append(stmt)
            current_stmt = []

    # Add any remaining statement
    if current_stmt:
        stmt = '\n'.join(current_stmt).strip()
        if stmt:
            statements.append(stmt)

    print(f"📊 Found {len(statements)} SQL statements to execute\n")

    client = boto3.client("rds-data", region_name=AWS_REGION)
    db_password = get_db_password()
    secret_arn = create_temp_secret(db_password)

    try:
        results = []
        for idx, sql in enumerate(statements, 1):
            print(f"▶️  Executing statement {idx}/{len(statements)}...")
            print(f"   {sql[:100]}{'...' if len(sql) > 100 else ''}")

            try:
                response = client.execute_statement(
                    resourceArn=AURORA_CLUSTER_ARN,
                    secretArn=secret_arn,
                    database=DB_NAME,
                    sql=sql,
                    includeResultMetadata=True,
                )

                records_updated = response.get('numberOfRecordsUpdated', 0)
                if records_updated > 0:
                    print(f"   ✅ {records_updated} records affected\n")
                else:
                    print(f"   ✅ Statement executed successfully\n")

                results.append({
                    "statement_num": idx,
                    "status": "success",
                    "records_updated": records_updated
                })

            except Exception as e:
                error_msg = str(e)

                # Check if it's an "already exists" error (can be ignored)
                ignorable_errors = [
                    "already exists",
                    "duplicate key value",
                    "SQLState: 42710",  # duplicate_object
                    "SQLState: 42P07",  # duplicate_table
                    "SQLState: 42723",  # duplicate_function
                ]

                is_ignorable = any(
                    err in error_msg for err in ignorable_errors)

                if is_ignorable:
                    print(
                        f"   ⚠️  Skipped (already exists): {error_msg.split('ERROR:')[1].split(';')[0] if 'ERROR:' in error_msg else error_msg[:80]}\n")
                    results.append({
                        "statement_num": idx,
                        "status": "skipped",
                        "reason": "already_exists"
                    })
                    # Continue to next statement
                else:
                    print(f"   ❌ Error: {error_msg}\n")
                    results.append({
                        "statement_num": idx,
                        "status": "error",
                        "error": error_msg
                    })
                    # Stop on actual error
                    print("⚠️  Migration stopped due to error")
                    break

        # Print summary
        print("\n" + "=" * 60)
        print("📊 Migration Results")
        print("=" * 60)
        successful = sum(1 for r in results if r['status'] == 'success')
        skipped = sum(1 for r in results if r['status'] == 'skipped')
        failed = sum(1 for r in results if r['status'] == 'error')
        print(f"Total statements:     {len(statements)}")
        print(f"✅ Successful:        {successful}")
        print(f"⚠️  Skipped:          {skipped}")
        print(f"❌ Failed:            {failed}")

        if failed > 0:
            print("\n⚠️  Migration completed with errors")
        else:
            if skipped > 0:
                print(
                    "\n✅ Migration completed successfully (some objects already existed)")
            else:
                print("\n✅ Migration completed successfully!")

        return results

    finally:
        # Always delete the temporary secret
        print("\n🗑️  Cleaning up temporary secret...")
        delete_secret(secret_arn)
        print("✅ Cleanup complete")


# -----------------------------
# Example run
# -----------------------------
if __name__ == "__main__":
    import sys

    # Default migration file path
    default_migration = "../../backend/shared/database/migrations/001_init.sql"

    if len(sys.argv) > 1:
        # Use migration file path from command line argument
        migration_file = sys.argv[1]
    else:
        # Use default migration file
        migration_file = default_migration

    print("=" * 60)
    print("🚀 Aurora Database Migration Script")
    print("=" * 60)
    print(f"Migration file: {migration_file}\n")

    try:
        run_migration(migration_file)
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
