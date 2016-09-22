"""Tests for SQL DAO implementations, using in-memory SQLite"""
import datetime

import pytest
import sqlalchemy as sa

from onix import contexts
from onix.dto import BattleInfo
from onix.scripts import log_generator as lg

from onix.backend.sql import model
from onix.backend.sql import sinks


@pytest.fixture(scope='module')
def context():
    return contexts.get_standard_context()


@pytest.fixture(scope='module')
def players():
    return [lg.generate_player(username, formatid='anythinggoes',
                               rpr=r, rprd=rd)[1]
            for (username, r, rd) in (('Alice', 1900., 25.),
                                      ('Bob', 1750., 31.),
                                      ('Charley', 1700., 75.),
                                      ('Delia', 1550., 100.),
                                      ('Eve', 1210., 25.))]


@pytest.fixture(scope='module')
def movesets(context):
    return [lg.generate_pokemon(species, context)[0]
            for species in ('articuno',
                            'beartic',
                            'cradily',
                            'druddigon',
                            'entei',
                            'furfrou',
                            'gallade',
                            'hypno',
                            'igglybuff',
                            'jirachi',
                            'klinklang',
                            'lilligant',
                            'jirachi',
                            'gallademega')]


@pytest.fixture()
def teams(movesets):
    return [movesets[:6],
            movesets[6:12],
            [movesets[i] for i in (6, 7, 8, 12, 10, 11)],
            [movesets[i] for i in (3, 5, 13, 8, 0, 1)],
            [movesets[i] for i in (5, 5, 5, 5, 5, 5)],
            [movesets[9]]]


@pytest.fixture()
def engine():
    return sa.create_engine('sqlite:///')


@pytest.fixture()
def initialize_db(engine):
    model.create_tables(engine)
    with engine.connect() as conn:
        conn.execute()
