#!/bin/bash
# PostgreSQL Setup Script for Stock Sentinel
# 
# This script creates the 'stocksentinel' user and database
# Run this as the 'postgres' user with admin privileges
#
# Usage on Windows (in PowerShell as Administrator):
#   psql -U postgres -f setup_postgres.sql
#
# Usage on Linux/Mac:
#   sudo -u postgres psql -f setup_postgres.sql

-- ============================================================================
-- STEP 1: Create the 'stocksentinel' user with password
-- ============================================================================
-- If user already exists, this will fail. See DROP USER command below.
CREATE USER stocksentinel WITH ENCRYPTED PASSWORD 'password';

-- ============================================================================
-- STEP 2: Grant connection privileges
-- ============================================================================
ALTER ROLE stocksentinel WITH LOGIN;

-- ============================================================================
-- STEP 3: Create the 'stocksentinel' database
-- ============================================================================
CREATE DATABASE stocksentinel OWNER stocksentinel;

-- ============================================================================
-- STEP 4: Grant privileges on the database
-- ============================================================================
GRANT ALL PRIVILEGES ON DATABASE stocksentinel TO stocksentinel;

-- ============================================================================
-- STEP 5: Connect to the newly created database and grant schema privileges
-- ============================================================================
-- This needs to be run while connected to the stocksentinel database
\c stocksentinel

-- Grant all schema privileges
GRANT ALL ON SCHEMA public TO stocksentinel;

-- Grant all table privileges (for future tables)
GRANT ALL ON ALL TABLES IN SCHEMA public TO stocksentinel;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO stocksentinel;

-- Grant all sequence privileges (for auto-increment IDs)
GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO stocksentinel;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO stocksentinel;

-- ============================================================================
-- STEP 6: Verify the setup
-- ============================================================================
-- List users
\du

-- List databases
\l

-- Show current database
SELECT current_database();

-- ============================================================================
-- TROUBLESHOOTING: If user already exists, use these commands first:
-- ============================================================================
-- DROP USER IF EXISTS stocksentinel;
-- This will fail if user owns objects. Use CASCADE:
-- DROP USER IF EXISTS stocksentinel CASCADE;

-- If database already exists:
-- DROP DATABASE IF EXISTS stocksentinel;

-- Reset password for existing user:
-- ALTER USER stocksentinel WITH ENCRYPTED PASSWORD 'password';
