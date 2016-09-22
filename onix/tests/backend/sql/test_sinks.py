"""Tests for SQL sink implementations, using in-memory SQLite"""
import datetime
import json

import pytest
import sqlalchemy as sa

from onix.dto import Moveset, Forme, PokeStats, Player, BattleInfo
from onix import scrapers
from onix import utilities
from onix.backend.sql import model
from onix.backend.sql import sinks


@pytest.fixture()
def sanitizer():
    try:
        pokedex = json.load(open('.psdata/pokedex.json'))
    except IOError:
        pokedex = scrapers.scrape_battle_pokedex()

    try:
        aliases = json.load(open('.psdata/aliases.json'))
    except IOError:
        aliases = scrapers.scrape_battle_aliases()

    return utilities.Sanitizer(pokedex, aliases)


@pytest.fixture()
def engine():
    return sa.create_engine('sqlite:///')


@pytest.fixture()
def initialize_db(engine):
    model.create_tables(engine)


@pytest.fixture()
def session_maker(engine):
    return sa.orm.sessionmaker(bind=engine)


class TestComputeTid(object):

    @staticmethod
    @pytest.fixture()
    def set_1():
        return Moveset([Forme('Blastoise-Mega', 'Mega Launcher',
                              PokeStats(361, 189, 276, 405, 268, 192)),
                        Forme('Blastoise', 'Rain Dish',
                              PokeStats(361, 153, 236, 295, 248, 192))],
                       'F', 'Blastoisinite',
                       ['Water Spout', 'Aura Sphere', 'Dragon Pulse',
                        'Dark Pulse'], 100, 255)

    @staticmethod
    @pytest.fixture()
    def set_2():
        return Moveset([Forme('gardevoir', 'synchronize',
                              PokeStats(340, 121, 251, 286, 266, 197))],
                       'u', 'choicescarf', ['healingwish'], 100, 255)

    @staticmethod
    @pytest.fixture()
    def original_tid(sanitizer, set_1, set_2):
        return sinks.compute_tid([set_1, set_2], sanitizer)

    def test_tid_equivalence(self, sanitizer, set_1, set_2, original_tid):

        set_1a = Moveset([Forme('Blastoise-Mega', 'Mega Launcher',
                                PokeStats(360, 189, 276, 405, 268, 193)),
                          Forme('Blastoise', 'Rain Dish',
                                PokeStats(360, 153, 236, 295, 248, 193))],
                         'F', 'Blastoisinite',
                         ['Water Spout', 'Aura Sphere', 'Dragon Pulse',
                          'Dark Pulse'], 100, 255)

        equivalent_tid = sinks.compute_tid([set_2, set_1], sanitizer)
        non_equivalent_tid = sinks.compute_tid([set_1a, set_2],  sanitizer)

        assert original_tid == equivalent_tid
        assert original_tid != non_equivalent_tid

    def test_compute_by_sids(self, sanitizer, set_1, set_2, original_tid):

        sid_1 = utilities.compute_sid(set_1, sanitizer)
        sid_2 = utilities.compute_sid(set_2, sanitizer)

        tid_by_sid = sinks.compute_tid([sid_1, sid_2])
        reversed = sinks.compute_tid([sid_2, sid_1])

        assert original_tid == tid_by_sid
        assert original_tid == reversed

    def test_invalid_type(self):

        with pytest.raises(TypeError):
            sinks.compute_tid([3, 6, 2])


def test_compute_fid(sanitizer):
    original_forme = Forme('magcargo', 'flamebody',
                           PokeStats(253, 133, 309, 210, 216, 86))
    equivalent_forme = Forme('Magcargo', 'Flame Body',
                             PokeStats(253, 133, 309, 210, 216, 86))
    non_equivalent_forme = Forme('magcargo', 'weakarmor',
                                 PokeStats(253, 133, 309, 210, 216, 86))

    original_fid = sinks.compute_fid(original_forme)
    equivalent_fid = sinks.compute_fid(equivalent_forme, sanitizer)
    non_equivalent_fid = sinks.compute_fid(non_equivalent_forme, sanitizer)

    assert original_fid == equivalent_fid
    assert original_fid != non_equivalent_fid


def test_convert_forme():
    forme = Forme('moltres', 'pressure',
                  PokeStats(349, 234, 208, 276, 239, 202))
    db_obj = sinks.convert_forme(forme)

    assert 'moltres' == db_obj.species
    assert 'pressure' == db_obj.ability
    assert 208 == db_obj.dfn


def test_convert_moveset():
    moveset = Moveset([Forme('tyranitar', 'sandstream',
                             PokeStats(342, 308, 278, 229, 238, 167)),
                       Forme('tyranitarmega', 'sandstream',
                             PokeStats(342, 368, 358, 229, 278, 187))],
                      'u', 'tyranitarite',
                      ['dragondance', 'earthquake', 'icepunch', 'stoneedge'],
                      100, 255)

    expected_sid = utilities.compute_sid(moveset)
    db_obj = sinks.convert_moveset(moveset)

    assert expected_sid == db_obj.id
    assert 'tyranitarite' == db_obj.item
    assert 'icepunch' == db_obj.moves[2].move
    assert 187 == db_obj.formes[1].spe


def test_convert_team():
    team_sids = ['6860d5bc287f6614',
                 '0c913e97615a85c6',
                 'f3993878e060a7f2',
                 '75c060c9501a1636',
                 '81c606d0d5f54719',
                 '68e4d3ac2171649d']

    expected_tid = sinks.compute_tid(team_sids)

    tid, db_objs = sinks.convert_team(team_sids)

    assert expected_tid == tid
    assert expected_tid == db_objs[3].tid
    assert 4 == db_objs[4].idx
    assert '0c913e97615a85c6' == db_objs[0].sid


def test_convert_player():
    player = Player('tazye', {'elo': 1135.3099468803014, 't': 3, 'l': 2,
                              'rprd': 52.57927168060377,
                              'rpr': 1568.6587994250103,
                              'rd': None, 'w': 63})

    db_obj = sinks.convert_player(player, 2, '5742af7b')
    assert 'tazye' == db_obj.pid
    assert 2 == db_obj.l
    assert db_obj.rd is None
    assert db_obj.r is None


def test_convert_battle_info():
    battle_info = BattleInfo(7535, 'anythinggoes', datetime.date(2016, 9, 15),
                             [Player('57fipp8', {'rd': 101.95, 'r': 1109.76}),
                              Player('i7iu7f', {'elo': 1358.67})],
                             [['af4b9d989ea24b91', '053976712b484401'],
                              ['053976712b484401', 'af4b9d989ea24b91']],
                             8, 'normal')

    db_objs = sinks.convert_battle_info(battle_info)

    assert 'anythinggoes' == db_objs[0].format
    assert 1109.76 == db_objs[0].players[0].r
    assert 2 == db_objs[0].players[1].side
    assert db_objs[1][1].tid == db_objs[1][3].tid
    assert db_objs[1][1].sid == db_objs[1][3].sid
    assert db_objs[1][1].idx == db_objs[1][3].idx


@pytest.mark.usefixtures('initialize_db')
class TestMovesetSink(object):

    @staticmethod
    @pytest.fixture()
    def sceptile():
        return Moveset([Forme('sceptile', 'overgrow',
                              PokeStats(293, 207, 149, 251, 198, 336))],
                       'u', 'lifeorb',
                       ['earthquake', 'gigadrain', 'leafblade', 'outrage'],
                       100, 255)

    @staticmethod
    @pytest.fixture()
    def mega_sceptile():
        return Moveset([Forme('sceptile', 'overgrow',
                              PokeStats(293, 207, 149, 251, 198, 336)),
                        Forme('sceptilemega', 'lightningrod',
                              PokeStats(293, 257, 169, 331, 198, 391))],
                       'u', 'sceptilite',
                       ['earthquake', 'gigadrain', 'leafblade', 'outrage'],
                       100, 255)

    @staticmethod
    @pytest.fixture()
    def chimchar():
        return Moveset([Forme('chimchar', 'ironfist',
                              PokeStats(21, 13, 11, 11, 11, 11))],
                       'u', 'focussash',
                       ['fakeout', 'hiddenpowerbug', 'overheat', 'stealthrock'],
                       5, 255)

    def test_insert_one(self, engine, session_maker, mega_sceptile):

        sid = utilities.compute_sid(mega_sceptile)
        with sinks.MovesetSink(session_maker) as moveset_sink:
            moveset_sink.store_movesets({sid: mega_sceptile})

        with engine.connect() as conn:
            result = conn.execute('SELECT COUNT(*) FROM movesets')
            assert (1,) == result.fetchone()
            result = conn.execute('SELECT COUNT(*) FROM formes')
            assert (2,) == result.fetchone()
            result = conn.execute('SELECT COUNT(*) FROM moveset_forme')
            assert (2,) == result.fetchone()
            result = conn.execute('SELECT COUNT(*) FROM moveslots')
            assert (4,) == result.fetchone()
            result = conn.execute('SELECT sid, idx FROM moveslots '
                                  'WHERE move == "earthquake"')
            assert (sid, 0) == result.fetchone()

    def test_insert_duplicates(self, engine, session_maker, chimchar):

        movesets = {utilities.compute_sid(chimchar): chimchar}
        with sinks.MovesetSink(session_maker) as moveset_sink:
            moveset_sink.store_movesets(movesets)
            moveset_sink.store_movesets(movesets)

        with engine.connect() as conn:
            result = conn.execute('SELECT COUNT(*) FROM movesets')
            assert (1,) == result.fetchone()
            result = conn.execute('SELECT COUNT(*) FROM formes')
            assert (1,) == result.fetchone()
            result = conn.execute('SELECT COUNT(*) FROM moveset_forme')
            print(list(conn.execute('SELECT * FROM moveset_forme')))
            assert (1,) == result.fetchone()
            result = conn.execute('SELECT COUNT(*) FROM moveslots')
            assert (4,) == result.fetchone()

    def test_insert_several(self, engine, session_maker,
                            sceptile, mega_sceptile, chimchar):

        movesets = {utilities.compute_sid(moveset): moveset
                    for moveset in [sceptile, mega_sceptile, chimchar]}

        with sinks.MovesetSink(session_maker) as moveset_sink:
            moveset_sink.store_movesets(movesets)

        with engine.connect() as conn:
            result = conn.execute('SELECT COUNT(*) FROM movesets')
            assert (3,) == result.fetchone()
            result = conn.execute('SELECT COUNT(*) FROM formes')
            assert (3,) == result.fetchone()
            result = conn.execute('SELECT COUNT(*) FROM moveset_forme')
            assert (4,) == result.fetchone()
            result = conn.execute('SELECT COUNT(*) FROM moveslots')
            assert (12,) == result.fetchone()

    def test_batch_size(self, engine, session_maker, sceptile, chimchar):

        with sinks.MovesetSink(session_maker, batch_size=2) as moveset_sink,\
                engine.connect() as conn:

            moveset_sink.store_movesets({utilities.compute_sid(sceptile):
                                         sceptile})

            result = conn.execute('SELECT COUNT(*) FROM movesets')
            assert (0,) == result.fetchone()
            assert 6 == len(list(moveset_sink.session))  # 1 ms + 1 fm + 4 mvs

            moveset_sink.store_movesets({utilities.compute_sid(chimchar):
                                         chimchar})

            result = conn.execute('SELECT COUNT(*) FROM movesets')
            assert (2,) == result.fetchone()
            assert 0 == len(list(moveset_sink.session))


@pytest.mark.usefixtures('initialize_db')
class TestBattleInfoSink(object):

    @staticmethod
    @pytest.fixture()
    def players():
        return [Player('alice', {'l': 57, 'w': 16, 't': 0}),
                Player('bob', {'l': 24, 'w': 23, 't': 4}),
                Player('eve', {'l': 68, 'w': 52, 't': 7})]

    @staticmethod
    @pytest.fixture()
    def teams():
        return [['7e3a6e07', '9cb1e085', 'ca66695c'],
                ['cedfdf7a', 'd92e68ec', '9cb1e085'],
                ['9cb1e085', '7e3a6e07', 'ca66695c']]


    @staticmethod
    @pytest.fixture()
    def battle_infos(players, teams):
        return [BattleInfo(1, 'ubers', datetime.date(2016, 9, 22),
                           players[:2], teams[:2],
                           14, 'normal'),
                BattleInfo(2, 'ubers', datetime.date(2016, 9, 22),
                           players[1:], teams[1:],
                           18, 'forfeit')]

    def test_insert_one(self, engine, session_maker, battle_infos):

        with sinks.BattleInfoSink(session_maker) as battle_info_sink:
            battle_info_sink.store_battle_info(battle_infos[0])

        with engine.connect() as conn:
            result = conn.execute('SELECT COUNT(*) FROM teams')
            assert (6,) == result.fetchone()
            result = conn.execute('SELECT COUNT(*) FROM battle_info')
            assert (1,) == result.fetchone()
            result = conn.execute('SELECT COUNT(*) FROM battle_player')
            assert (2,) == result.fetchone()
            result = conn.execute('SELECT bid, side FROM battle_player '
                                  'WHERE pid == "bob"')
            assert (1, 2) == result.fetchone()

    def test_insert_duplicates(self, engine, session_maker, battle_infos):

        with sinks.BattleInfoSink(session_maker) as battle_info_sink:
            battle_info_sink.store_battle_info(battle_infos[1])
            battle_info_sink.store_battle_info(battle_infos[1])

        with engine.connect() as conn:
            result = conn.execute('SELECT COUNT(*) FROM teams')
            assert (6,) == result.fetchone()
            result = conn.execute('SELECT COUNT(*) FROM battle_info')
            assert (1,) == result.fetchone()
            result = conn.execute('SELECT COUNT(*) FROM battle_player')
            assert (2,) == result.fetchone()

    def test_insert_several(self, engine, session_maker, battle_infos):

        with sinks.BattleInfoSink(session_maker) as battle_info_sink:
            battle_info_sink.store_battle_info(battle_infos[0])
            battle_info_sink.store_battle_info(battle_infos[1])

        with engine.connect() as conn:
            result = conn.execute('SELECT COUNT(*) FROM teams')
            assert (6,) == result.fetchone()
            result = conn.execute('SELECT COUNT(DISTINCT tid) FROM teams')
            assert (2,) == result.fetchone()
            result = conn.execute('SELECT COUNT(*) FROM battle_info')
            assert (2,) == result.fetchone()
            result = conn.execute('SELECT COUNT(*) FROM battle_player')
            assert (4,) == result.fetchone()
            result = conn.execute('SELECT COUNT(DISTINCT pid) '
                                  'FROM battle_player')
            assert (3,) == result.fetchone()

    def test_batch_size(self, engine, session_maker, battle_infos):

        with sinks.BattleInfoSink(session_maker, 2) as battle_info_sink,\
                 engine.connect() as conn:
            battle_info_sink.store_battle_info(battle_infos[0])
            result = conn.execute('SELECT COUNT(*) FROM battle_info')
            assert (0,) == result.fetchone()
            assert 9 == len(list(battle_info_sink.session))  # 1 bi + 2 p + 6 tm
            battle_info_sink.store_battle_info(battle_infos[1])
            result = conn.execute('SELECT COUNT(*) FROM battle_info')
            assert (2,) == result.fetchone()
            assert 0 == len(list(battle_info_sink.session))





