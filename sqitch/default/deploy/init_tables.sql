-- Deploy default:init_tables to pg

BEGIN;

CREATE TABLE books (
  id                    SERIAL       NOT NULL PRIMARY KEY,
  safari_book_id        INT          NOT NULL DEFAULT 0,
  reviews               INT          NOT NULL DEFAULT 0,
  rating                SMALLINT     NOT NULL DEFAULT 0,
  title                 VARCHAR(255) NOT NULL,
  tag                   VARCHAR(255) NOT NULL DEFAULT '',
  created_time          TIMESTAMP WITHOUT TIME ZONE DEFAULT (CURRENT_TIMESTAMP AT TIME ZONE 'UTC')
);
CREATE UNIQUE INDEX books_safari_book_id ON books (safari_book_id);
CREATE UNIQUE INDEX books_title ON books ((lower(title)));
CREATE UNIQUE INDEX books_tag ON books ((lower(tag)));


COMMIT;
