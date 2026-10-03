

    Migration : Guardian and Doctor users are migrated to the new Users table. 
    what is done in this migration:
    1. Add user_id to guardian and doc table 
    2. Created the user records for existing guardians , doctors 
    3.Linked the guardian.user_id to users.user_id
    4. Linked the doctor.user_id to users.user_id
    6. Converted eisting vaishnavi anfdf kishan which was orignally in user table to admin usertype .

=====================================

  ALTER TABLE guardian
ADD COLUMN IF NOT EXISTS user_id INTEGER
REFERENCES users(user_id);  
================================

ALTER TABLE doctor
ADD COLUMN IF NOT EXISTS user_id INTEGER
REFERENCES users(user_id);

========================================
Guardian authentication details:
--   mobile_number  -> username
--   password_hash  -> password
--   parent         -> user_type


Step 3 : Migrate existing GUARDIAN records into USERS

query : 
INSERT INTO users (
    username,
    password,
    user_type,
    is_active,
    created_at,
    updated_at,
    first_name,
    last_name
)
SELECT
    g.mobile_number,
    g.password_hash,
    'parent',
    g.is_active,
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP,
    g.first_name,
    g.last_name
FROM guardian AS g
WHERE g.mobile_number IS NOT NULL
  AND NOT EXISTS (
      SELECT 1
      FROM users AS u
      WHERE u.username = g.mobile_number
  );


  ==============================================

  4. Migrate existing DOCTOR records into USERS
--
-- Doctor authentication details:
--   staff_id       -> username
--   password_hash  -> password
--   doctor         -> user_type

Query : 
INSERT INTO users (
    username,
    password,
    user_type,
    is_active,
    created_at,
    updated_at,
    first_name,
    last_name
)
SELECT
    d.staff_id,
    d.password_hash,
    'doctor',
    d.is_active,
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP,
    d.first_name,
    d.last_name
FROM doctor AS d
WHERE d.staff_id IS NOT NULL
  AND NOT EXISTS (
      SELECT 1
      FROM users AS u
      WHERE u.username = d.staff_id
  );

=========================================

5 . LINKED GUARDIAN RECORDS TO USERS 
Query :


UPDATE guardian AS g
SET user_id = u.user_id
FROM users AS u
WHERE u.username = g.mobile_number
  AND u.user_type = 'parent'
  AND (
      g.user_id IS NULL
      OR g.user_id <> u.user_id
  );

==============================================


C:\Users\asus\OneDrive\Desktop\Pedia-center-backend\migrations\001_migrate_guardian_doctor_to_users.sql

001_ is useful because database migrations are normally executed in sequence.

2. Complete migration file

Put the following entire SQL into that file:

-- ============================================================
-- Migration: Guardian and Doctor authentication migration
-- File: 001_migrate_guardian_doctor_to_users.sql
-- Purpose:
--   1. Add user_id to guardian and doctor tables
--   2. Create users records from existing guardians
--   3. Create users records from existing doctors
--   4. Link guardian.user_id to users.user_id
--   5. Link doctor.user_id to users.user_id
--   6. Convert existing Vaishnavi and Kishan users to admin
-- ============================================================


BEGIN;


-- ============================================================
-- 1. Add user_id to GUARDIAN table
-- ============================================================

ALTER TABLE guardian
ADD COLUMN IF NOT EXISTS user_id INTEGER
REFERENCES users(user_id);


-- ============================================================
-- 2. Add user_id to DOCTOR table
-- ============================================================

ALTER TABLE doctor
ADD COLUMN IF NOT EXISTS user_id INTEGER
REFERENCES users(user_id);


-- ============================================================
-- 3. Migrate existing GUARDIAN records into USERS
--
-- Guardian authentication details:
--   mobile_number  -> username
--   password_hash  -> password
--   parent         -> user_type
-- ============================================================

INSERT INTO users (
    username,
    password,
    user_type,
    is_active,
    created_at,
    updated_at,
    first_name,
    last_name
)
SELECT
    g.mobile_number,
    g.password_hash,
    'parent',
    g.is_active,
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP,
    g.first_name,
    g.last_name
FROM guardian AS g
WHERE g.mobile_number IS NOT NULL
  AND NOT EXISTS (
      SELECT 1
      FROM users AS u
      WHERE u.username = g.mobile_number
  );


-- ============================================================
-- 4. Migrate existing DOCTOR records into USERS
--
-- Doctor authentication details:
--   staff_id       -> username
--   password_hash  -> password
--   doctor         -> user_type
-- ============================================================

INSERT INTO users (
    username,
    password,
    user_type,
    is_active,
    created_at,
    updated_at,
    first_name,
    last_name
)
SELECT
    d.staff_id,
    d.password_hash,
    'doctor',
    d.is_active,
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP,
    d.first_name,
    d.last_name
FROM doctor AS d
WHERE d.staff_id IS NOT NULL
  AND NOT EXISTS (
      SELECT 1
      FROM users AS u
      WHERE u.username = d.staff_id
  );


-- ============================================================
-- 5. Link GUARDIAN records to USERS
-- ============================================================

UPDATE guardian AS g
SET user_id = u.user_id
FROM users AS u
WHERE u.username = g.mobile_number
  AND u.user_type = 'parent'
  AND (
      g.user_id IS NULL
      OR g.user_id <> u.user_id
  );


-- ============================================================
-- 6. Link DOCTOR records to USERS
-- ============================================================

UPDATE doctor AS d
SET user_id = u.user_id
FROM users AS u
WHERE u.username = d.staff_id
  AND u.user_type = 'doctor'
  AND (
      d.user_id IS NULL
      OR d.user_id <> u.user_id
  );
============================================================================

-- 7. Change existing Vaishnavi and Kishan users to ADMIN
-- ============================================================

UPDATE users
SET user_type = 'admin'
WHERE user_id IN (1, 2);


-- ============================================================
-- 8. Verification: USERS
-- ============================================================

SELECT
    user_id,
    username,
    user_type,
    first_name,
    last_name,
    is_active
FROM users
ORDER BY user_id;


-- ============================================================
-- 9. Verification: GUARDIAN -> USERS
-- ============================================================

SELECT
    g.guardian_id,
    g.mobile_number,
    g.first_name,
    g.last_name,
    g.user_id,
    u.user_id AS users_user_id,
    u.username,
    u.user_type
FROM guardian AS g
LEFT JOIN users AS u
    ON g.user_id = u.user_id
ORDER BY g.guardian_id;


-- ============================================================
-- 10. Verification: DOCTOR -> USERS
-- ============================================================

SELECT
    d.doctor_id,
    d.staff_id,
    d.first_name,
    d.last_name,
    d.user_id,
    u.user_id AS users_user_id,
    u.username,
    u.user_type
FROM doctor AS d
LEFT JOIN users AS u
    ON d.user_id = u.user_id
ORDER BY d.doctor_id;