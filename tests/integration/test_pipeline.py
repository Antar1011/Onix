"""Tests the entire Onix workflow"""
from __future__ import division
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
def single_log(tmpdir, ctx):
    """
    Generates a single log and returns a path to the log

    Returns:
        py.path.local : the absolute path to the generated log
    """
    log_path = (tmpdir.mkdir('logs').mkdir('2016-09')
                .mkdir('ou')
                .mkdir('2016-09-30')
                .join('battle-ou-134134.log.json'))

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

    players = [lg.generate_player('alice', rpr=3000., rprd=50.)[0],
               lg.generate_player('bob', rpr=1630., rprd=50.)[0]]

    json.dump(lg.generate_log(players, teams, 36, 'normal'),
              open(log_path.strpath, 'w+'))

    return log_path


@pytest.fixture()
def log_folder(tmpdir, ctx):
    """
    Generates a bunch of log and returns a path to the containing directory

    Returns:
        py.path.local : the absolute path to the log folder
    """
    log_folder = tmpdir.mkdir('logs')
    meta_folder = log_folder.mkdir('2016-10').mkdir('ubers')

    for i in range(1, 32):
        meta_folder.mkdir('2016-10-{0:02}'.format(i))

    pokemon = [('zygarde', 2),
               ('yanmega', 4),
               ('xerneas', 5),
               ('wailord', 2),
               ('volcarona', 6),
               ('umbreon', 4),
               ('tornadustherian', 5),
               ('swampertmega', 2),
               ('registeel', 3),
               ('quagsire', 8),
               ('pidgeotmega', 5),
               ('octillery', 1),
               ('nidoking', 3),
               ('moltres', 7)]

    movesets = [[lg.generate_pokemon(species, ctx)[0] for _ in range(num)]
                for species, num in pokemon]

    teams = [[random.choice(mon_sets)
              for mon_sets in random.sample(movesets, 6)]
             for _ in range(100)]

    names = ('Alice', 'Bob', 'Charley', 'Delia', 'Eve', 'Frank', 'Geoff',
             'Harold', 'Igor', 'Josephine')

    end_types = ('normal', 'forfeit')

    for i in range(1000):
        log = lg.generate_log([lg.generate_player(random.choice(names))[0]
                               for _ in range(2)],
                              random.sample(teams, 2),
                              random.randint(6, 128),
                              random.choice(end_types))
        path = meta_folder.join('2016-10-{0:02}'.format(
            31 * i // 1000 + 1)).join('battle-ubers-{0}.log.json'.format(i))
        json.dump(log, open(path.strpath, 'w+'))

    return log_folder


class TestSqlBackendPipeline(object):

    def test_single_log(self, engine, single_log, ctx):

        with engine.connect() as conn:
            with sinks.MovesetSink(conn) as ms, sinks.BattleInfoSink(conn) as bs:
                processor = LogProcessor(ms, bs, None)

                processor.process_logs(single_log.strpath, ref_type='file')

        with engine.connect() as conn:
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

    @pytest.mark.slow
    def test_log_folder(self, engine, log_folder, ctx):
        with engine.connect() as conn:
            with sinks.MovesetSink(conn) as ms, sinks.BattleInfoSink(
                    conn) as bs:
                processor = LogProcessor(ms, bs, None)

                processor.process_logs(log_folder.strpath)

        with engine.connect() as conn:
            rd = dao.ReportingDAO(conn)
            report = generate_usage_stats(rd, ctx.species_lookup,
                                          '201610', 'ubers', baseline=0)

        lines = report.split('\n')
        assert 21 == len(lines)  # 14 mons
        assert ' Total battles: 1000' == lines[0]
        assert ' Avg. weight / team: 1.000000' == lines[1]

