# Copyright (c) 2018 App Annie Inc. All rights reserved.

"""
get sqlalchemy session
"""

import logging
import traceback
from functools import wraps

from enum import Enum

try:
    from urllib import quote_plus
except:
    from urllib.parse import quote_plus

from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import scoped_session
from sqlalchemy.pool import QueuePool

import safaribooks.settings

logger = logging.getLogger(__name__)


def get_connection_string(db_conf):
    """Get the connection string for the database alias.

    :param dict conf: the database config.
    :rtype: str
    :return: The connection string.
    """
    return ('postgresql://{0}:{1}@{2}:{3}/{4}'.format(
        db_conf.get('USER'),
        quote_plus(db_conf.get('PASSWORD')),
        db_conf.get('HOST'),
        db_conf.get('PORT'),
        db_conf.get('NAME')
    ))


def get_session(db_conf, debug=False, application_name="default", statement_timeout=5000,
                pool_recycle=-1, pool_size=1, isolation_level=None):
    """Get session

    :param dict db_conf: a dict to describe the config of database.
                         The template is:
                         ``{'ENGINE': 'pg', 'NAME': 'postgres', 'USER': 'postgres', 'PASSWORD': 'xx',
                            'HOST': 'aa-postgres', 'PORT': '5432', 'OPTIONS': {'autocommit': False},}``.
    :param bool debug: Set echo parameter in create_engine which is used to log all statements.
    :param string application_name: Set application_name parameter in create_engine.
    :param int statement_timeout: Cancel statement due to statement timeout.
    :param int pool_recycle: Causes the pool to recycle connections after the given number of seconds.
    :param int pool_size: the number of connections to keep open inside the connection pool. Default is 5.
    :param string isolation_level: Affect the transaction isolation level of the database connection.
                                   Default is None. You could set it as 'AUTOCOMMIT' to enable real autocommit.
    :rtype: scoped_session
    :return: Session with bound engine.
    """
    try:
        engine = create_engine(
            get_connection_string(db_conf),
            poolclass=QueuePool,
            pool_recycle=pool_recycle,  # recycle connections after 30 minutes
            pool_size=pool_size,
            echo=debug,
            connect_args={
                "application_name": application_name,
                "options": "-c statement_timeout={}".format(statement_timeout),
            },
            isolation_level=isolation_level
        )

        autocommit = db_conf.get('OPTIONS', {}).get("autocommit", True)
        session = scoped_session(sessionmaker())
        session.configure(
            bind=engine,
            autocommit=autocommit,
        )
    except:
        logger.exception("config_session failed, conf: %s", db_conf)
        raise
    return session


class TransactionIsolationLevel(Enum):
    AUTOCOMMIT = 'AUTOCOMMIT'
    READ_WRITE = 'READ COMMITTED'
    REPEATABLE_READ = 'REPEATABLE READ'
    SERIALIZABLE = 'SERIALIZABLE'


def create_db_session(isolation_level=TransactionIsolationLevel.READ_WRITE):
    """
    :param db: database name
    :type db: str
    :param isolation_level:
    :type isolation_level: str
    :return: db session
    :rtype: Session
    """
    return get_session(safaribooks.settings.DATABASE, isolation_level=isolation_level.value)()


SESSION = create_db_session()  # type: Session


def with_transaction(wrapped_fn):
    """
    This decorator is used for inner_service.appcare_manager
    :return:
    :rtype:
    """

    @wraps(wrapped_fn)
    def _decorator(*args, **kwargs):
        try:
            SESSION.begin(subtransactions=True)
            res = wrapped_fn(*args, **kwargs)
            SESSION.commit()
            return res
        except Exception:
            SESSION.rollback()
            logger.error(traceback.format_exc())
            raise

    return _decorator
