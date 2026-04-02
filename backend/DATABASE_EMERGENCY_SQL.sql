-- ===========================================================================
-- Stock Sentinel Database Emergency Cleanup & Diagnostic Script
-- ===========================================================================
-- 
-- This file contains various SQL commands for:
-- 1. Diagnosing database state
-- 2. Emergency cleanup (development only!)
-- 3. Fixing orphaned constraints/indexes
-- 4. Resetting sequences
--
-- IMPORTANT: These are for DEVELOPMENT ONLY!
-- Use alembic migrations for production database management.
--
-- ===========================================================================

-- ===========================================================================
-- SECTION 1: DIAGNOSTIC QUERIES
-- ===========================================================================

-- Check current database state
SELECT current_database() as database_name;
SELECT current_user as connected_as;

-- List all tables
SELECT table_name FROM information_schema.tables 
WHERE table_schema = 'public' 
ORDER BY table_name;

-- Check specific table structure (example: alerts table)
-- SELECT column_name, data_type, is_nullable, column_default
-- FROM information_schema.columns
-- WHERE table_name = 'alerts'
-- ORDER BY ordinal_position;

-- List all indexes
SELECT indexname, tablename 
FROM pg_indexes 
WHERE schemaname = 'public'
ORDER BY tablename, indexname;

-- Check for duplicate indexes
SELECT tablename, indexname, indexdef
FROM pg_indexes
WHERE schemaname = 'public'
ORDER BY tablename, indexname;

-- List all foreign keys
SELECT 
    kcu.table_name,
    kcu.column_name,
    ccu.table_name AS foreign_table_name,
    ccu.column_name AS foreign_column_name,
    rc.constraint_name
FROM information_schema.key_column_usage AS kcu
JOIN information_schema.constraint_column_usage AS ccu
  ON kcu.constraint_name = rc.constraint_name
JOIN information_schema.referential_constraints rc
  ON kcu.constraint_name = rc.constraint_name
WHERE kcu.table_schema = 'public'
ORDER BY kcu.table_name, kcu.column_name;

-- Check for NULL values in 'condition' column (alerts table)
-- SELECT COUNT(*) as null_count FROM alerts WHERE condition IS NULL;
-- SELECT COUNT(*) as total_count FROM alerts;

-- ===========================================================================
-- SECTION 2: MIGRATION STATUS CHECK
-- ===========================================================================

-- Check alembic_version table (migration history)
-- SELECT * FROM alembic_version;

-- ===========================================================================
-- SECTION 3: EMERGENCY CLEANUP (DEVELOPMENT ONLY!)
-- ===========================================================================

-- ⚠️  WARNING: These operations DELETE ALL DATA
-- ⚠️  Only run in development environments!
-- ⚠️  Always backup before running!

-- Option A: Drop all tables (keeps sequences, types)
-- DROP TABLE IF EXISTS alert_history CASCADE;
-- DROP TABLE IF EXISTS portfolio_stocks CASCADE;
-- DROP TABLE IF EXISTS watchlist_stocks CASCADE;
-- DROP TABLE IF EXISTS portfolios CASCADE;
-- DROP TABLE IF EXISTS watchlists CASCADE;
-- DROP TABLE IF EXISTS sentiment_records CASCADE;
-- DROP TABLE IF EXISTS stock_predictions CASCADE;
-- DROP TABLE IF EXISTS alerts CASCADE;
-- DROP TABLE IF EXISTS stocks CASCADE;
-- DROP TABLE IF EXISTS users CASCADE;
-- DELETE FROM alembic_version;

-- Option B: Drop EVERYTHING (tables, types, sequences) - complete reset
-- BEGIN;
--   DROP TABLE IF EXISTS alert_history CASCADE;
--   DROP TABLE IF EXISTS portfolio_stocks CASCADE;
--   DROP TABLE IF EXISTS watchlist_stocks CASCADE;
--   DROP TABLE IF EXISTS portfolios CASCADE;
--   DROP TABLE IF EXISTS watchlists CASCADE;
--   DROP TABLE IF EXISTS sentiment_records CASCADE;
--   DROP TABLE IF EXISTS stock_predictions CASCADE;
--   DROP TABLE IF EXISTS alerts CASCADE;
--   DROP TABLE IF EXISTS stocks CASCADE;
--   DROP TABLE IF EXISTS users CASCADE;
--   DROP TYPE IF EXISTS alertcondition CASCADE;
--   DROP TYPE IF EXISTS alerttype CASCADE;
--   DROP SEQUENCE IF EXISTS users_id_seq CASCADE;
--   DROP SEQUENCE IF EXISTS alerts_id_seq CASCADE;
--   DROP SEQUENCE IF EXISTS stocks_id_seq CASCADE;
--   DELETE FROM alembic_version;
-- COMMIT;

-- ===========================================================================
-- SECTION 4: FIX SPECIFIC ISSUES
-- ===========================================================================

-- Fix NULL values in 'condition' column before making NOT NULL
-- UPDATE alerts SET condition = 'GREATER_THAN' WHERE condition IS NULL;

-- Drop orphaned indexes (if they exist with wrong names)
-- DROP INDEX IF EXISTS idx_alert_history_user_id;
-- DROP INDEX IF EXISTS idx_alert_history_alert_id;
-- DROP INDEX IF EXISTS idx_alerts_is_triggered;
-- DROP INDEX IF EXISTS idx_alerts_last_triggered_at;

-- Rename index (if needed for migration compatibility)
-- ALTER INDEX old_index_name RENAME TO new_index_name;

-- Drop and recreate a specific index
-- DROP INDEX IF EXISTS ix_alerts_user_id;
-- CREATE INDEX ix_alerts_user_id ON alerts(user_id);

-- ===========================================================================
-- SECTION 5: RESET SEQUENCES (for auto-increment IDs)
-- ===========================================================================

-- Reset sequence to max ID + 1 for a table
-- SELECT setval('users_id_seq', (SELECT MAX(id) FROM users) + 1);
-- SELECT setval('alerts_id_seq', (SELECT MAX(id) FROM alerts) + 1);
-- SELECT setval('stocks_id_seq', (SELECT MAX(id) FROM stocks) + 1);

-- ===========================================================================
-- SECTION 6: VERIFY DATABASE STATE AFTER FIXES
-- ===========================================================================

-- Count rows in each table
SELECT 
    schemaname,
    tablename,
    (SELECT count(*) FROM pg_class c 
     WHERE c.relname = t.tablename AND c.relkind = 'r') as row_count
FROM pg_tables t
WHERE schemaname = 'public'
ORDER BY tablename;

-- Check for missing indexes (indexes defined in models but not in DB)
-- SELECT * FROM pg_indexes 
-- WHERE schemaname = 'public' AND tablename IN ('alerts', 'alert_history', 'users')
-- ORDER BY tablename, indexname;

-- ===========================================================================
-- PRODUCTION SAFE APPROACH
-- ===========================================================================

-- NEVER run emergency cleanup in production!
-- Use Alembic migrations instead:
--
-- 1. To add a column:
--    alembic revision --autogenerate -m "add column_name to table_name"
--    Review and apply: alembic upgrade head
--
-- 2. To drop a column:
--    alembic revision --autogenerate -m "drop column_name from table_name"
--    Review and apply: alembic upgrade head
--
-- 3. To create an index:
--    Edit model, add to __table_args__, then:
--    alembic revision --autogenerate -m "add indexes for table_name"
--    Review and apply: alembic upgrade head
--
-- 4. To rollback in production:
--    alembic downgrade -1  # Go back one migration
--    alembic current       # See current state

