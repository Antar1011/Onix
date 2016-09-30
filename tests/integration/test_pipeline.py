"""Tests the entire Onix workflow"""
import json
import random

import pytest
import sqlalchemy as sa

from onix import contexts
from onix.collection.log_processor import LogProcessor
from onix.backend.sql.schema import create_tables
from onix.backend.sql import sinks
from onix.backend.sql import dao
from onix.reporting.reports import generate_usage_stats

from onix.scripts import log_generator as lg


@pytest.fixture()
def engine(tmpdir):
    engine = sa.create_engine('sqlite:///{0}/onix.sqlite'.format(
        tmpdir.strpath))

    create_tables(engine)
    return engine

@pytest.fixture()
def ctx():
    return contexts.get_standard_context()


@pytest.fixture()
def log_folder(tmpdir, ctx):
    """
    Generates logs and returns the location where the logs are stored

    Returns:
        str : the absolute path to the directory containing the stored logs
    """
    log_folder = tmpdir.mkdir('logs')

    movesets = [lg.generate_pokemon(species, ctx)[0]
                for species in ('aerodactyl',  # 0
                                'aerodactylmega',  # 1
                                'blissey',  # 2
                                'clawitzer',  # 3
                                'dragalge',  # 4
                                'espeon',  # 5
                                'espeon',  # 6
                                'froslass',  # 7
                                'gigalith',  # 8
                                'hydreigon',  # 9
                                'illumise')]  # 10

    teams = [[movesets[i] for i in setnums]
             for setnums in ((0, 2, 3, 4, 5, 7),
                             (4, 6, 7, 8, 9, 10))]

    players = [lg.generate_player('alice', rpr=3000.)[0],
               lg.generate_player('bob', rpr=1630.)[0]]

    log = lg.generate_log(players, teams, 36, 'normal')
    json.dump(log, open(log_folder.mkdir('2016-09').mkdir('ou')
                        .mkdir('2016-09-30')
                        .join('battle-ou-134134.log.json').strpath, 'w+'))

    return log_folder


def test_sql_backend_pipeline(engine, log_folder, ctx):

    with engine.connect() as conn:
        with sinks.MovesetSink(conn) as ms, sinks.BattleInfoSink(conn) as bs:
            processor = LogProcessor(ms, bs, None)

            processor.process_logs(log_folder.strpath)

        rd = dao.ReportingDAO(conn)

        expected = ' Total battles: 1\n'\
                   ' Avg. weight / team: 0.750000\n'\
                   ' + ---- + ------------------------- + --------- +\n'\
                   ' | Rank | Species                   | Usage %   |\n'\
                   ' + ---- + ------------------------- + --------- +\n'\
                   ' |    1 | Dragalge                  | 100.0000% |\n'\
                   ' |    2 | Espeon                    | 100.0000% |\n'\
                   ' |    3 | Froslass                  | 100.0000% |\n'\
                   ' |    4 | Aerodactyl                |  66.6667% |\n'\
                   ' |    5 | Blissey                   |  66.6667% |\n'\
                   ' |    6 | Clawitzer                 |  66.6667% |\n'\
                   ' |    7 | Gigalith                  |  33.3333% |\n'\
                   ' |    8 | Hydreigon                 |  33.3333% |\n'\
                   ' |    9 | Illumise                  |  33.3333% |\n'\
                   ' + ---- + ------------------------- + --------- +\n'

        assert expected == generate_usage_stats(rd, ctx.species_lookup,
                                                '201609', 'ou')

