-- Manually creates (or updates) the guest demo account in verity.users.
--
-- This script is NOT run by Alembic, CI/CD, or any deploy pipeline.
-- Run it yourself, locally, against the target database:
--   psql "$DATABASE_URL" -f scripts/create_guest_user.sql
--
-- Before running:
--   1. Replace REPLACE_WITH_GUEST_EMAIL and REPLACE_WITH_GUEST_PASSWORD below with real values.
--   2. Do not commit this file with real values filled in.
--
-- Uses pgcrypto's crypt()/gen_salt('bf', 12) to produce a bcrypt hash in the same
-- $2a$/$2b$ format the app's passlib CryptContext(schemes=["bcrypt"]) already verifies,
-- so no separate Python step is needed.
--
-- The role column stores a comma-separated list to preserve the same multi-role
-- access the old one-click guest login granted (see backend/src/verity_portal/identity/router.py).

CREATE EXTENSION IF NOT EXISTS pgcrypto;

INSERT INTO verity.users (id, email, hashed_password, is_active, role)
VALUES (
    gen_random_uuid(),
    'REPLACE_WITH_GUEST_EMAIL',
    crypt('REPLACE_WITH_GUEST_PASSWORD', gen_salt('bf', 12)),
    true,
    'guest,ROLE_HR,ROLE_PM,ROLE_ECO,ROLE_FINANCE,ROLE_IT'
)
ON CONFLICT (email) DO UPDATE
SET hashed_password = EXCLUDED.hashed_password,
    role = EXCLUDED.role,
    is_active = true;
