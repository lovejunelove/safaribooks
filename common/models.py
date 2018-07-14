from datetime import datetime
from sqlalchemy.dialects import postgresql
from sqlalchemy import Column, DateTime, Integer, VARCHAR, TEXT, SMALLINT
from sqlalchemy.ext.declarative import declarative_base

from common.db_session import SESSION, with_transaction

BASE = declarative_base()


class BookStatus():
    NOT_DOWNLOADED = 0
    DOWNLOADING = 1
    DOWNLOADED = 2
    UPLOADING = 3
    UPLOADED = 4


class ModelBooks(BASE):
    __tablename__ = 'books'

    id = Column(Integer, primary_key=True)
    safari_book_id = Column(VARCHAR(32), nullable=False)
    status = Column(
        SMALLINT, nullable=False, default=0
    )  # 4, uploaded, 3 uploading, 2 downloaded, 1 downloading, 0 not downloaded
    reviews = Column(Integer, nullable=False, default=0)
    rating = Column(Integer, nullable=False, default=0)
    popularity = Column(Integer, nullable=False, default=0)
    report_score = Column(Integer, nullable=False, default=0)
    pages = Column(Integer, nullable=False, default=0)
    title = Column(TEXT, nullable=False, default='')
    description = Column(TEXT, nullable=False, default='')
    language = Column(VARCHAR(255), nullable=False, default='')
    authors = Column(postgresql.JSONB, default=[])
    publishers = Column(postgresql.JSONB, default=[])
    tags = Column(postgresql.JSONB, default=[])
    url = Column(VARCHAR(4096), nullable=False, default='')
    web_url = Column(VARCHAR(4096), nullable=False, default='')
    created_time = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return "<ModelBooks(id={})>".format(self.id)

    @staticmethod
    @with_transaction
    def get_a_book(status=BookStatus.NOT_DOWNLOADED, next_status=BookStatus.DOWNLOADING):
        model = SESSION.query(ModelBooks).filter(ModelBooks.status == status).limit(1).one_or_none()
        if not model:
            return None

        model.status = next_status
        SESSION.flush()
        return model

    @staticmethod
    @with_transaction
    def finish(safari_book_id, status=BookStatus.DOWNLOADED):
        model = SESSION.query(ModelBooks).filter(ModelBooks.safari_book_id == safari_book_id).one_or_none()
        if not model:
            return
        model.status = status
        SESSION.flush()
