# RDS IAM Auth — How It Works

How the Lambda authenticates to RDS Postgres without storing a password.

## Two-layer check

1. **AWS IAM** — Lambda role allowed to call `rds-db:connect` for user `habitadmin`. Set in `template.yaml`.
2. **Postgres** — DB user must have `rds_iam` role granted inside Postgres. Without it, Postgres treats IAM token as a regular password → mismatch → `InvalidPasswordError`.

CloudFormation can't run SQL inside the DB. Only Postgres itself can `GRANT rds_iam`. One-time manual psql bootstrap is required after stack create.

## Token generation vs validation

Two separate things — easy to confuse.

### 1. Token generation (AWS-side)

- `boto3.rds.generate_db_auth_token()` in `src/core/db.py`
- Needs IAM permission `rds-db:connect`
- Lambda role does this
- **No Postgres role involved** — AWS just signs a string
- 15-min TTL baked into the signed string

### 2. Token validation (Postgres-side, per connection)

Postgres sees user `habitadmin`, checks: "does this role have `rds_iam`?"
- Yes → call RDS service, verify token signature + TTL + IAM perms → allow/deny
- No → treat as password → hash compare → fail

`rds_iam` role = **"validate as IAM token, not password"** flag on the DB user. Per-connection check, not per-token.

## Diagram

```
Lambda                                RDS Postgres
  │                                       │
  ├─ generate_db_auth_token() ──► AWS ────┤  (token = signed string, 15min)
  │                                       │
  ├─ asyncpg.connect(password=token) ────►│  user=habitadmin
  │                                       ├─ has rds_iam?
  │                                       │   yes → verify token w/ AWS ✓
  │                                       │   no  → bcrypt compare ✗ → InvalidPasswordError
```

## Why role-based?

Postgres auth methods set per-user in `pg_hba.conf`. RDS adds a custom method `rds_iam`. RDS can't modify `pg_hba.conf` per-user easily, so it uses Postgres's own role system as the toggle:

```
host all <users-with-rds_iam-role>  all  cert  rds_iam
host all <other-users>              all  scram-sha-256
```

Grant `rds_iam` to a user → that user's auth flips from password-hash compare to IAM token validation.

## Bootstrap (one-time after stack create)

Bash / Git Bash:

```bash
STACK=habit-tracker

SECRET_ARN=$(aws cloudformation describe-stacks --stack-name "$STACK" \
  --query "Stacks[0].Outputs[?OutputKey=='DBMasterSecretArn'].OutputValue" \
  --output text)

DB_HOST=$(aws cloudformation describe-stacks --stack-name "$STACK" \
  --query "Stacks[0].Outputs[?OutputKey=='DBEndpoint'].OutputValue" \
  --output text)

PGPASSWORD=$(aws secretsmanager get-secret-value --secret-id "$SECRET_ARN" \
  --query SecretString --output text | jq -r .password)

export PGPASSWORD
psql "host=$DB_HOST port=5432 dbname=habittracker user=habitadmin sslmode=require" \
  -c "GRANT rds_iam TO habitadmin;"
```

Note: granting `rds_iam` to the master user works but is unconventional. Cleaner pattern is a separate `app_user`:

```sql
CREATE USER app_user;
GRANT rds_iam TO app_user;
GRANT CONNECT ON DATABASE habittracker TO app_user;
GRANT USAGE ON SCHEMA public TO app_user;
GRANT ALL ON ALL TABLES IN SCHEMA public TO app_user;
GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO app_user;
```

Then update `template.yaml` env `DB_USER: app_user` and the IAM policy `Resource` ARN's `dbuser/` suffix → `app_user`. Redeploy.

## Verify

`rds_iam` is a Postgres role — invisible to AWS console/CLI. Check via psql:

```sql
-- All users with rds_iam granted
SELECT rolname FROM pg_auth_members m
JOIN pg_roles r ON m.roleid = r.oid
JOIN pg_roles u ON m.member = u.oid
WHERE r.rolname = 'rds_iam';

-- Single user
SELECT pg_has_role('habitadmin', 'rds_iam', 'MEMBER');
```

Empty result / `f` → role not granted → expect `InvalidPasswordError` on connect.

## Symptom of missing grant

```
GET /health → {"status":"unhealthy","database":"error","error_class":"InvalidPasswordError"}
```

asyncpg sends the IAM token as the password. Postgres falls through to scram-sha-256 (no `rds_iam` grant), the token doesn't match the stored hash, connection rejected.

## Related files

- `src/core/db.py` — `_inject_iam_token` event listener, generates fresh token per connection
- `src/infrastructure/aws/lambda_entry.py` — builds `DATABASE_URL` without a password
- `template.yaml` — `EnableIAMDatabaseAuthentication: true`, `rds-db:connect` policy
