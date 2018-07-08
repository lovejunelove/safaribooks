from datetime import datetime
from sqlalchemy.dialects import postgresql
from sqlalchemy import Column, DateTime, Integer, VARCHAR, TEXT, SMALLINT
from sqlalchemy.ext.declarative import declarative_base

BASE = declarative_base()


class ModelBooks(BASE):
    __tablename__ = 'books'

    id = Column(Integer, primary_key=True)
    safari_book_id = Column(VARCHAR(32), nullable=False)
    status = Column(SMALLINT, nullable=False, default=0)  # 1 downloaded, 0 not downloaded
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
