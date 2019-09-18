import os

import pandas as pd
from sqlalchemy import create_engine

from db_config import (
    SCHEMA
)

_DEFAULT_DB_NAME = 'postgres'


def _get_local_host_url(db_name=_DEFAULT_DB_NAME):
    url = 'postgresql://{usr}:{password}@localhost:5432/{db_name}'.format(usr=os.environ['POSTGRES_USR'],
                                                                          password=os.environ['POSTGRES_PASSWORD'],
                                                                          db_name=db_name)
    return url


def create_postgres_engine(url=_get_local_host_url()):
    engine = create_engine(url)
    return engine


def make_query(q, conn):
    df = pd.read_sql(q, conn)
    return df


def write_to_db(df,
                conn,
                table_name,
                schema=SCHEMA,
                if_exists='fail'):
    df.to_sql(table_name,
              conn,
              schema=schema,
              if_exists=if_exists,
              index=False,
              method='multi',
              )


# def purge_all_tables(conn,
#                      tables=[PERSON_META_TABLE,
#                              PERSON_EXPERIENCE_TABLE,
#                              PERSON_SUMMARY_TABLE,
#                              PERSON_SPECIALTY_TABLE],
#                      schema=SCHEMA):
#     # Use with care!
#     for t in tables:
#         q = """
#         DROP TABLE {schema}.{table}
#         """.format(schema=schema, table=t)
#
#         _ = make_query(q, conn)
#         print('drop table {schema}.{table}'.format(schema=schema, table=t))
#
#     return
