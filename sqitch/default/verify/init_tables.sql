-- Verify default:init_tables on pg

BEGIN;

-- XXX Add verifications here.
SELECT COUNT(1) FROM books;

ROLLBACK;
