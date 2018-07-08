-- Revert default:init_tables from pg

BEGIN;

-- XXX Add DDLs here.
DROP TABLE books;

COMMIT;
