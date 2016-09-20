"""Tests for the model module for the SQL backend"""
import pytest
import sqlalchemy as sa

from onix.backend.sql import model


@pytest.fixture()
def engine():
    """
    Creates an engine for an in-memory Sqlite DB

    Returns:
        sqlalchemy.engine.Engine :
            The DB engine
    """
    return sa.create_engine('sqlite:///')


@pytest.fixture()
def initialize_db(engine):
    """
    Initialize the database with all the various tables

    Returns:
        None
    """
    model.create_tables(engine)


@pytest.mark.usefixtures('initialize_db')
class TestCreateTables(object):

    def test_schema(self, engine):

        # just testing that one of the tables has the right colnames
        expected = ['id', 'gender', 'item', 'level', 'happiness']

        moveset_schema = list(engine.execute('PRAGMA table_info([movesets])'))

        assert expected == [column[1] for column in moveset_schema]

    def test_foreign_key_constraint(self, engine):
        with pytest.raises(sa.exc.IntegrityError):
            engine.execute('INSERT INTO moveset_forme VALUES("ac","gg")')

    def test_insert_or_ignore(self, engine):
        ins = model.Base.metadata.tables['battle_info'].insert()
        with engine.connect() as conn:
            conn.execute(ins.values(id=1, format='ou'))
            conn.execute(ins.values(id=1, format='uu'))
        result = engine.execute('SELECT id, format from battle_info')

        assert [(1, 'ou')] == list(result)




