from sqlalchemy import (
    BOOLEAN, Column, MetaData, SMALLINT, String, Table
)

from db_config import (
    LOCATION_COUNTRY_TABLE,
    PERSON_EXPERIENCE_TABLE, PERSON_META_TABLE,
    PERSON_SPECIALTY_TABLE, PERSON_SUMMARY_TABLE, SCHEMA
)
from utils.db_util import create_postgres_engine


sql_engine = create_postgres_engine()
metadata = MetaData(bind=sql_engine)

if not sql_engine.dialect.has_table(sql_engine, PERSON_EXPERIENCE_TABLE, schema=SCHEMA):
    Table(PERSON_EXPERIENCE_TABLE,
          metadata,
          Column('person_id', String, primary_key=True),
          Column('experience_id', SMALLINT, primary_key=True),
          Column('org_name', String),
          Column('org_profile_link', String),
          Column('org_detail', String),
          Column('experience_title', String),
          Column('experience_location', String),
          Column('experience_description', String),
          Column('date_start', String),
          Column('date_end', String),
          Column('duration', String),
          Column('is_current', BOOLEAN),
          schema=SCHEMA)

if not sql_engine.dialect.has_table(sql_engine, PERSON_META_TABLE, schema=SCHEMA):
    Table(PERSON_META_TABLE,
          metadata,
          Column('person_id', String, primary_key=True),
          Column('parent_folder', String),
          Column('batch_folder', String),
          Column('given_name', String),
          Column('family_name', String),
          Column('header_title', String),
          Column('header_location', String),
          Column('header_industry', String),
          schema=SCHEMA)

if not sql_engine.dialect.has_table(sql_engine, PERSON_SUMMARY_TABLE, schema=SCHEMA):
    Table(PERSON_SUMMARY_TABLE,
          metadata,
          Column('person_id', String, primary_key=True),
          Column('person_summary', String),
          schema=SCHEMA)

if not sql_engine.dialect.has_table(sql_engine, PERSON_SPECIALTY_TABLE, schema=SCHEMA):
    Table(PERSON_SPECIALTY_TABLE,
          metadata,
          Column('person_id', String, primary_key=True),
          Column('person_specialty', String),
          schema=SCHEMA)

if not sql_engine.dialect.has_table(sql_engine, LOCATION_COUNTRY_TABLE, schema=SCHEMA):
    Table(LOCATION_COUNTRY_TABLE,
          metadata,
          Column('header_location', String, primary_key=True),
          Column('country', String),
          schema=SCHEMA)

metadata.create_all()
