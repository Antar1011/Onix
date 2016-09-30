"""Tests on the database schema for the SQL backend"""
import pytest
import sqlalchemy as sa

from onix.backend.sql import schema


@pytest.fixture()
def engine():
    return sa.create_engine('sqlite:///')


@pytest.fixture()
def initialize_db(engine):
    schema.create_tables(engine)


@pytest.mark.usefixtures('initialize_db')
class TestCreateTables(object):

    def test_schema(self, engine):

        # just testing that one of the tables has the right colnames
        expected = ['id', 'gender', 'item', 'level', 'happiness']

        moveset_schema = list(engine.execute('PRAGMA table_info([movesets])'))

        assert expected == [column[1] for column in moveset_schema]

    def test_foreign_key_constraint(self, engine):
        with pytest.raises(sa.exc.IntegrityError):
            engine.execute('INSERT INTO moveset_forme VALUES("ac","gg", 1)')

    def test_insert_or_ignore(self, engine):
        ins = schema.battle_infos.insert()
        with engine.connect() as conn:
            conn.execute(ins.values(id=1, format='ou'))
            conn.execute(ins.values(id=1, format='uu'))
        result = engine.execute('SELECT id, format from battle_infos')

        assert [(1, 'ou')] == list(result)




