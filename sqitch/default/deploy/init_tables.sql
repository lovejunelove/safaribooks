-- Deploy default:init_tables to pg

BEGIN;

CREATE TABLE books (
  id                    SERIAL       NOT NULL PRIMARY KEY,
  safari_book_id        INT          NOT NULL,
  reviews               INT          NOT NULL DEFAULT 0,
  rating                INT          NOT NULL DEFAULT 0,
  popularity            INT          NOT NULL DEFAULT 0,
  report_score          INT          NOT NULL DEFAULT 0,
  pages                 INT          NOT NULL DEFAULT 0,
  title                 VARCHAR(255) NOT NULL DEFAULT '',
  language              VARCHAR(255) NOT NULL DEFAULT '',
  authors               JSONB,
  publishers            JSONB,
  tag                   JSONB,
  description           TEXT,
  url                   VARCHAR(255) NOT NULL DEFAULT '',
  web_url               VARCHAR(255) NOT NULL DEFAULT '',
  created_time          TIMESTAMP WITHOUT TIME ZONE DEFAULT (CURRENT_TIMESTAMP AT TIME ZONE 'UTC')
);
CREATE UNIQUE INDEX books_safari_book_id ON books (safari_book_id);
CREATE UNIQUE INDEX books_title ON books ((lower(title)));
CREATE UNIQUE INDEX books_tag ON books ((lower(tag)));


COMMIT;
