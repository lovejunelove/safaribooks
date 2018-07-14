-- Deploy default:init_tables to pg

BEGIN;

CREATE TABLE books (
  id                    SERIAL       NOT NULL PRIMARY KEY,
  safari_book_id        VARCHAR(32)  NOT NULL,
  status                SMALLINT     NOT NULL DEFAULT 0, --  4, uploaded, 3 uploading, 2 downloaded, 1 downloading, 0 not downloaded
  reviews               INT          NOT NULL DEFAULT 0,
  rating                INT          NOT NULL DEFAULT 0,
  popularity            INT          NOT NULL DEFAULT 0,
  report_score          INT          NOT NULL DEFAULT 0,
  pages                 INT          NOT NULL DEFAULT 0,
  title                 TEXT         NOT NULL DEFAULT '',
  description           TEXT         NOT NULL DEFAULT '',
  language              VARCHAR(255) NOT NULL DEFAULT '',
  authors               JSONB,
  publishers            JSONB,
  tags                  JSONB,
  url                   VARCHAR(4096) NOT NULL DEFAULT '',
  web_url               VARCHAR(4096) NOT NULL DEFAULT '',
  created_time          TIMESTAMP WITHOUT TIME ZONE DEFAULT (CURRENT_TIMESTAMP AT TIME ZONE 'UTC')
);
CREATE UNIQUE INDEX books_safari_book_id ON books (safari_book_id);
CREATE INDEX books_title ON books ((lower(title)));
CREATE INDEX books_authors ON books (authors);
CREATE INDEX books_publishers ON books (publishers);
CREATE INDEX books_tag ON books (tags);


COMMIT;
