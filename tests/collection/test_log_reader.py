"""Tests for log readers and related functions"""
import json
import os
import shutil

import pytest

from onix import contexts
from onix import utilities

from onix.model import PokeStats, Moveset, Player, Forme
from onix.collection import log_reader


class StumpLogReader(log_reader.LogReader):

    def __init__(self, context, metagame):
        super(StumpLogReader,
              self).__init__(context)

        (self.game_type,
         self.hackmons,
         self.any_ability,
         self.mega_rayquaza_allowed,
         self.default_level) = utilities.parse_ruleset(
            context.formats[metagame])

    def _parse_log(self, log_ref):
        pass


@pytest.fixture(scope='class')
def ctx():
    return contexts.get_standard_context()


class TestGetAllFormes(object):

    def test_pokemon_with_a_single_forme(self, ctx):

        expected = [Forme('stunfisk', 'static',
                          PokeStats(109, 66, 84, 81, 99, 32))]
        assert expected == log_reader.get_all_formes('stunfisk', 'static', None,
                                                     ['voltswitch'],
                                                     ctx)

    def test_pokemon_with_wrong_ability(self, ctx):

        expected = [Forme('vileplume', 'chlorophyll',
                          PokeStats(75, 80, 85, 110, 90, 50))]
        assert expected == log_reader.get_all_formes('vileplume', 'flashfire',
                                                     'absorbbulb',
                                                     ['gigadrain'],
                                                     ctx)

    def test_pokemon_with_wrong_ability_in_hackmons(self, ctx):

        expected = [Forme('vileplume', 'flashfire',
                          PokeStats(75, 80, 85, 110, 90, 50))]
        assert expected == log_reader.get_all_formes('vileplume', 'flashfire',
                                                     'absorbbulb',
                                                     ['gigadrain'],
                                                     ctx, True, True)

    def test_pokemon_with_wrong_ability_in_aaa(self, ctx):

        expected = [Forme('vileplume', 'flashfire',
                          PokeStats(75, 80, 85, 110, 90, 50))]
        assert expected == log_reader.get_all_formes('vileplume', 'flashfire',
                                                     'absorbbulb',
                                                     ['gigadrain'],
                                                     ctx, False, True)

    def test_pokemon_with_mega_forme(self, ctx):

        expected = [Forme('venusaur', 'chlorophyll',
                          PokeStats(80, 82, 83, 100, 100, 80)),
                    Forme('venusaurmega', 'thickfat',
                          PokeStats(80, 100, 123, 122, 120, 80))]

        assert set(expected) == set(
            log_reader.get_all_formes('venusaur', 'chlorophyll',
                                      'venusaurite', ['frenzyplant'],
                                      ctx))
        assert set(expected) == set(
            log_reader.get_all_formes('venusaurmega', 'chlorophyll',
                                      'venusaurite', ['frenzyplant'],
                                      ctx))

    def test_pokemon_with_multiple_mega_formes(self, ctx):

        expected = [Forme('charizard', 'blaze',
                          PokeStats(78, 84, 78, 109, 85, 100)),
                    Forme('charizardmegay', 'drought',
                          PokeStats(78, 104, 78, 159, 115, 100))]

        assert set(expected) == set(
            log_reader.get_all_formes('charizard', 'blaze', 'charizarditey',
                                      ['blastburn'],
                                      ctx))

    def test_mega_mon_without_stone(self, ctx):

        expected = [Forme('venusaur', 'chlorophyll',
                          PokeStats(80, 82, 83, 100, 100, 80))]

        assert expected == log_reader.get_all_formes('venusaur', 'chlorophyll',
                                                     'leftovers',
                                                     ['frenzyplant'],
                                                     ctx)

        assert expected == log_reader.get_all_formes('venusaurmega',
                                                     'chlorophyll',
                                                     'leftovers',
                                                     ['frenzyplant'],
                                                     ctx)

    def test_mega_mon_without_stone_in_hackmons(self, ctx):

        expected = [Forme('venusaurmega', 'chlorophyll',
                          PokeStats(80, 100, 123, 122, 120, 80))]

        assert expected == log_reader.get_all_formes('venusaurmega',
                                                     'chlorophyll',
                                                     'leftovers',
                                                     ['frenzyplant'],
                                                     ctx, True, True)

    def test_mega_evolving_mega_in_hackmons(self, ctx):

        expected = [Forme('mewtwomegax', 'steadfast',
                          PokeStats(106, 190, 100, 154, 100, 130)),
                    Forme('mewtwomegay', 'marvelscale',
                          PokeStats(106, 150, 70, 194, 120, 140))
                    ]

        assert set(expected) == set(
            log_reader.get_all_formes('mewtwomegay', 'marvelscale',
                                      'mewtwonitex', ['psychic'],
                                      ctx, True, True))

    def test_aegislash_blade_in_hackmons(self, ctx):

        expected = [Forme('aegislash', 'stancechange',
                          PokeStats(60, 50, 150, 50, 150, 60)),
                    Forme('aegislashblade', 'stancechange',
                          PokeStats(60, 150, 50, 150, 50, 60))]

        assert set(expected) == set(
            log_reader.get_all_formes('aegislashblade', 'stancechange', None,
                                      ['kingsshield'],
                                      ctx, True, True))

        expected = [Forme('aegislashblade', 'stancechange',
                          PokeStats(60, 150, 50, 150, 50, 60))]

        assert set(expected) == set(
            log_reader.get_all_formes('aegislashblade', 'stancechange', None,
                                      ['shadowball'],
                                      ctx, True, True))

        expected = [Forme('aegislashblade', 'contrary',
                          PokeStats(60, 150, 50, 150, 50, 60))]

        assert set(expected) == set(
            log_reader.get_all_formes('aegislashblade', 'contrary', None,
                                      ['kingsshield'],
                                      ctx, True, True))

    def test_unrecognized_condition_type(self, ctx):

        ctx.accessible_formes['zapdos'] = [[{'because':
                                                 'i feel like it'},
                                            ['moltres']]]
        log_reader.get_all_formes('quilava', 'flashfire', None, ['flamewheel'],
                                  ctx)

        with pytest.raises(ValueError):
            log_reader.get_all_formes('zapdos', 'pressure', 'leftovers',
                                      ['voltswitch'],
                                      ctx)


class TestHiddenPowerNormalization(object):

    def test_correct_hidden_power(self):
        moves = ['earthquake', 'grassknot', 'hiddenpowerfire', 'rapidspin']
        ivs = PokeStats(31, 30, 31, 30, 31, 30)

        expected = ['earthquake', 'grassknot', 'hiddenpowerfire', 'rapidspin']

        assert expected == log_reader.normalize_hidden_power(moves, ivs)

    def test_no_hidden_power(self):
        moves = ['earthquake', 'grassknot', 'rapidspin']
        ivs = PokeStats(31, 30, 31, 30, 31, 30)

        expected = ['earthquake', 'grassknot', 'rapidspin']

        assert expected == log_reader.normalize_hidden_power(moves, ivs)

    def test_wrong_hidden_power(self):
        moves = ['earthquake', 'grassknot', 'hiddenpowerice', 'rapidspin']
        ivs = PokeStats(31, 30, 31, 30, 31, 30)

        expected = ['earthquake', 'grassknot', 'hiddenpowerfire', 'rapidspin']

        assert expected == log_reader.normalize_hidden_power(moves, ivs)

    def test_hidden_power_no_type(self):
        moves = ['earthquake', 'grassknot', 'hiddenpower', 'rapidspin']
        ivs = PokeStats(31, 30, 31, 30, 31, 30)

        expected = ['earthquake', 'grassknot', 'hiddenpowerfire', 'rapidspin']

        assert expected == log_reader.normalize_hidden_power(moves, ivs)


class TestMovesetParsing(object):

    def test_bare_bones_moveset(self, ctx):
        reader = StumpLogReader(ctx, 'ou')
        moveset_dict = json.loads('{"name":"Regirock","species":"Regirock",'
                                  '"item":"","ability":"Clear Body",'
                                  '"moves":["ancientpower"],"nature":"",'
                                  '"ivs":{"hp":31,"atk":0,"def":31,"spa":31,'
                                  '"spd":31,"spe":31},"evs":{"hp":0,"atk":0,'
                                  '"def":0,"spa":0,"spd":0,"spe":0}}')

        expected = Moveset([Forme('regirock', 'clearbody',
                                  PokeStats(301, 205, 436, 136, 236, 136))],
                           'u', None, ['ancientpower'], 100, 255)

        moveset = reader._parse_moveset(moveset_dict, reader.hackmons,
                                        reader.any_ability,
                                        reader.mega_rayquaza_allowed,
                                        reader.default_level)

        assert expected == moveset
        assert moveset == ctx.sanitizer.sanitize(moveset)

    def test_typical_moveset(self, ctx):
        reader = StumpLogReader(ctx, 'ou')
        moveset_dict = json.loads('{"name":"Cuddles","species":"ferrothorn",'
                                  '"item":"rockyhelmet","ability":"Iron Barbs",'
                                  '"moves":["stealthrock","leechseed",'
                                  '"gyroball","knockoff"],"nature":"Relaxed",'
                                  '"evs":{"hp":252,"atk":4,"def":252,"spa":0,'
                                  '"spd":0,"spe":0},"gender":"F","ivs":'
                                  '{"hp":31,"atk":31,"def":31,"spa":31,'
                                  '"spd":31,"spe":0},"shiny":true}')

        expected = Moveset([Forme('ferrothorn', 'ironbarbs',
                                  PokeStats(352, 225, 397, 144, 268, 40))],
                           'f', 'rockyhelmet',
                           ['gyroball', 'knockoff', 'leechseed', 'stealthrock'],
                           100, 255)

        moveset = reader._parse_moveset(moveset_dict, reader.hackmons,
                                        reader.any_ability,
                                        reader.mega_rayquaza_allowed,
                                        reader.default_level)

        assert expected == moveset
        assert moveset == ctx.sanitizer.sanitize(moveset)

    def test_standard_mega_evolving_moveset(self, ctx):
        reader = StumpLogReader(ctx, 'ou')
        moveset_dict = json.loads('{"name":"Gardevoir","species":"Gardevoir",'
                                  '"item":"gardevoirite",'
                                  '"ability":"Trace",'
                                  '"moves":["healingwish"],"nature":"Bold",'
                                  '"evs":{"hp":252,"atk":0,"def":252,"spa":0,'
                                  '"spd":0,"spe":4},"ivs":{"hp":31,"atk":0,'
                                  '"def":31,"spa":31,"spd":31,"spe":31}}')

        expected = Moveset([Forme('gardevoir', 'trace',
                                  PokeStats(340, 121, 251, 286, 266, 197)),
                            Forme('gardevoirmega', 'pixilate',
                                  PokeStats(340, 157, 251, 366, 306, 237))],
                           'u', 'gardevoirite', ['healingwish'], 100, 255)

        moveset = reader._parse_moveset(moveset_dict, reader.hackmons,
                                        reader.any_ability,
                                        reader.mega_rayquaza_allowed,
                                        reader.default_level)

        assert expected == moveset
        assert moveset == ctx.sanitizer.sanitize(moveset)

    def test_little_cup(self, ctx):
        reader = StumpLogReader(ctx, 'lc')
        moveset_dict = json.loads('{"name":"Chinchou","species":"Chinchou",'
                                  '"item":"airballoon","ability":"Volt Absorb",'
                                  '"moves":["charge","discharge","scald",'
                                  '"thunderwave"],"nature":"Modest",'
                                  '"evs":{"hp":4,"atk":0,"def":0,"spa":252,'
                                  '"spd":0,"spe":252},"gender":"M","level":5,'
                                  '"ivs":{"hp":31,"atk":31,"def":31,"spa":31,'
                                  '"spd":31,"spe":31}}')

        expected = Moveset([Forme('chinchou', 'voltabsorb',
                                  PokeStats(24, 9, 10, 16, 12, 16))],
                           'm', 'airballoon',
                           ['charge', 'discharge', 'scald', 'thunderwave'],
                           5, 255)

        moveset = reader._parse_moveset(moveset_dict, reader.hackmons,
                                        reader.any_ability,
                                        reader.mega_rayquaza_allowed,
                                        reader.default_level)

        assert expected == moveset
        assert moveset == ctx.sanitizer.sanitize(moveset)

    def test_improperly_mega_moveset(self, ctx):
        reader = StumpLogReader(ctx, 'ou')
        moveset_dict = json.loads('{"name":"Gardevoir",'
                                  '"species":"Gardevoirmega",'
                                  '"item":"choicescarf",'
                                  '"ability":"Pixilate",'
                                  '"moves":["healingwish"],"nature":"Bold",'
                                  '"evs":{"hp":252,"atk":0,"def":252,"spa":0,'
                                  '"spd":0,"spe":4},"ivs":{"hp":31,"atk":0,'
                                  '"def":31,"spa":31,"spd":31,"spe":31}}')

        expected = Moveset([Forme('gardevoir', 'synchronize',
                                 PokeStats(340, 121, 251, 286, 266, 197))],
                           'u', 'choicescarf',
                           ['healingwish'], 100, 255)

        moveset = reader._parse_moveset(moveset_dict, reader.hackmons,
                                        reader.any_ability,
                                        reader.mega_rayquaza_allowed,
                                        reader.default_level)

        assert expected == moveset
        assert moveset == ctx.sanitizer.sanitize(moveset)

    def test_mega_rayquaza_banned_from_ubers(self, ctx):
        reader = StumpLogReader(ctx, 'ubers')
        moveset_dict = json.loads('{"level": 100, "evs": {"spd": 252, '
                                  '"def": 40, "hp": 40, "spe": 12, "atk": 60, '
                                  '"spa": 104}, "item": "lifeorb", "species": '
                                  '"Rayquaza-Mega", "nature": "Relaxed", '
                                  '"ability": "Delta Stream", "ivs": '
                                  '{"spd": 23, "def": 14, "hp": 30, "spe": 3, '
                                  '"atk": 28, "spa": 28}, '
                                  '"moves": ["swordsdance", "extremespeed", '
                                  '"dragonascent", "vcreate"], '
                                  '"name": "Rayquaza-Mega"}'
)
        expected = Moveset([Forme('rayquaza', 'airlock',
                                  PokeStats(360, 348, 229, 359, 271, 180))],
                           'u', 'lifeorb', ['dragonascent', 'extremespeed',
                                            'swordsdance', 'vcreate'], 100, 255)

        moveset = reader._parse_moveset(moveset_dict, reader.hackmons,
                                        reader.any_ability,
                                        reader.mega_rayquaza_allowed,
                                        reader.default_level)

        assert expected == moveset
        assert moveset == ctx.sanitizer.sanitize(moveset)

    def test_mega_rayquaza_allowed_in_anything_goes(self, ctx):
        reader = StumpLogReader(ctx, 'anythinggoes')
        moveset_dict = json.loads('{"level": 100, "evs": {"spd": 252, '
                                  '"def": 40, "hp": 40, "spe": 12, "atk": 60, '
                                  '"spa": 104}, "item": "lifeorb", "species": '
                                  '"Rayquaza-Mega", "nature": "Relaxed", '
                                  '"ability": "Delta Stream", "ivs": '
                                  '{"spd": 23, "def": 14, "hp": 30, "spe": 3, '
                                  '"atk": 28, "spa": 28}, '
                                  '"moves": ["swordsdance", "extremespeed", '
                                  '"dragonascent", "vcreate"], '
                                  '"name": "Rayquaza-Mega"}')

        expected = Moveset([Forme('rayquaza', 'airlock',
                                  PokeStats(360, 348, 229, 359, 271, 180)),
                            Forme('rayquazamega', 'deltastream',
                                  PokeStats(360, 408, 251, 419, 291, 216))],
                           'u', 'lifeorb', ['dragonascent', 'extremespeed',
                                            'swordsdance', 'vcreate'], 100, 255)

        moveset = reader._parse_moveset(moveset_dict, reader.hackmons,
                                        reader.any_ability,
                                        reader.mega_rayquaza_allowed,
                                        reader.default_level)

        assert expected == moveset
        assert moveset == ctx.sanitizer.sanitize(moveset)

    def test_hackmons_moveset(self, ctx):
        reader = StumpLogReader(ctx, 'balancedhackmons')
        moveset_dict = json.loads('{"species": "Charizard-Mega-Y", "ivs": '
                                  '{"hp": 12, "spd": 10, "spa": 25, "atk": 20, '
                                  '"spe": 17, "def": 15}, "level": 100, '
                                  '"moves": ["roost", "willowisp", '
                                  '"flareblitz", "dragondance"], "evs": '
                                  '{"hp": 60, "spd": 60, "spa": 88, "atk": 20, '
                                  '"spe": 208, "def": 72}, "item": '
                                  '"charizarditex", "name": '
                                  '"Charry", "nature": "Impish", '
                                  '"ability": "drought"}')

        expected = Moveset([Forme('charizardmegay', 'drought',
                                  PokeStats(293, 238, 213, 333, 260, 274)),
                            Forme('charizardmegax', 'toughclaws',
                                  PokeStats(293, 290, 286, 280, 200, 274))],
                           'u', 'charizarditex',
                           ['dragondance', 'flareblitz', 'roost',
                            'willowisp'], 100, 255)

        moveset = reader._parse_moveset(moveset_dict, reader.hackmons,
                                        reader.any_ability,
                                        reader.mega_rayquaza_allowed,
                                        reader.default_level)

        assert expected == moveset
        assert moveset == ctx.sanitizer.sanitize(moveset)


class TestMovesetParsingWithMissingValues(object):

    @staticmethod
    @pytest.fixture()
    def moveset_dict():
        return json.loads('{"name":"Cuddles","species":"ferrothorn",'
                          '"item":"rockyhelmet","ability":"Iron Barbs",'
                          '"moves":["stealthrock","leechseed",'
                          '"gyroball","knockoff"],"nature":"Relaxed",'
                          '"evs":{"hp":252,"atk":4,"def":252,"spa":0,'
                          '"spd":0,"spe":0},"gender":"F","ivs":'
                          '{"hp":31,"atk":31,"def":31,"spa":31,'
                          '"spd":31,"spe":0},"shiny":true}')

    @staticmethod
    @pytest.fixture()
    def expected():
        return Moveset([Forme('ferrothorn', 'ironbarbs',
                              PokeStats(352, 225, 397, 144, 268, 40))],
                       'f', 'rockyhelmet',
                       ['gyroball', 'knockoff', 'leechseed', 'stealthrock'],
                       100, 255)

    @staticmethod
    @pytest.fixture()
    def reader(ctx):
        return StumpLogReader(ctx, 'ou')

    def test_missing_item(self, ctx, reader, moveset_dict, expected):

        del moveset_dict['item']

        expected = expected._replace(item=None)

        moveset = reader._parse_moveset(moveset_dict, reader.hackmons,
                                        reader.any_ability,
                                        reader.mega_rayquaza_allowed,
                                        reader.default_level)

        assert expected == moveset
        assert moveset == ctx.sanitizer.sanitize(moveset)

    def test_missing_ability(self, ctx, reader, moveset_dict, expected):

        del moveset_dict['ability']

        expected = expected._replace(
            formes=[expected.formes[0]._replace(ability='ironbarbs')])

        moveset = reader._parse_moveset(moveset_dict, reader.hackmons,
                                        reader.any_ability,
                                        reader.mega_rayquaza_allowed,
                                        reader.default_level)

        assert expected == moveset
        assert moveset == ctx.sanitizer.sanitize(moveset)

    def test_missing_nature(self, ctx, reader, moveset_dict, expected):

        del moveset_dict['nature']

        expected = expected._replace(
            formes=[expected.formes[0]._replace(
                stats=PokeStats(352, 225, 361, 144, 268, 45))])

        moveset = reader._parse_moveset(moveset_dict, reader.hackmons,
                                        reader.any_ability,
                                        reader.mega_rayquaza_allowed,
                                        reader.default_level)

        assert expected == moveset
        assert moveset == ctx.sanitizer.sanitize(moveset)

    def test_invalid_nature(self, ctx, reader, moveset_dict, expected):

        moveset_dict['nature'] = 'asdgrtgq'

        expected = expected._replace(
            formes=[expected.formes[0]._replace(
                stats=PokeStats(352, 225, 361, 144, 268, 45))])

        moveset = reader._parse_moveset(moveset_dict, reader.hackmons,
                                        reader.any_ability,
                                        reader.mega_rayquaza_allowed,
                                        reader.default_level)

        assert expected == moveset
        assert moveset == ctx.sanitizer.sanitize(moveset)

    def test_missing_ivs(self, ctx, reader, moveset_dict, expected):

        del moveset_dict['ivs']

        expected = expected._replace(
            formes=[expected.formes[0]._replace(
                stats=PokeStats(352, 225, 397, 144, 268, 68))])

        moveset = reader._parse_moveset(moveset_dict, reader.hackmons,
                                        reader.any_ability,
                                        reader.mega_rayquaza_allowed,
                                        reader.default_level)

        assert expected == moveset
        assert moveset == ctx.sanitizer.sanitize(moveset)

    def test_missing_evs(self, ctx, reader, moveset_dict, expected):

        del moveset_dict['evs']

        expected = expected._replace(
            formes=[expected.formes[0]._replace(
                stats=PokeStats(289, 224, 327, 144, 268, 40))])

        moveset = reader._parse_moveset(moveset_dict, reader.hackmons,
                                        reader.any_ability,
                                        reader.mega_rayquaza_allowed,
                                        reader.default_level)

        assert expected == moveset
        assert moveset == ctx.sanitizer.sanitize(moveset)

    def test_invalid_level(self, ctx, reader, moveset_dict, expected):

        for level in (-32, 'blue'):
            moveset_dict['level'] = level

            moveset = reader._parse_moveset(moveset_dict, reader.hackmons,
                                            reader.any_ability,
                                            reader.mega_rayquaza_allowed,
                                            reader.default_level)

            assert expected == moveset
            assert moveset == ctx.sanitizer.sanitize(moveset)

    def test_invalid_happiness(self, ctx, reader, moveset_dict, expected):

        for happiness in (-32, 'blue', 256):
            moveset_dict['happiness'] = happiness

            moveset = reader._parse_moveset(moveset_dict, reader.hackmons,
                                            reader.any_ability,
                                            reader.mega_rayquaza_allowed,
                                            reader.default_level)

            assert expected == moveset
            assert moveset == ctx.sanitizer.sanitize(moveset)


class TestPlayerParsing(object):

    def test_typical_player(self):
        ratings_dict = json.loads('{"rptime": 1465462800,"oldelo": "1000",'
                                  '"sigma": "0","formatid": "ou","col1": 2,'
                                  '"username": "sus_testing",'
                                  '"userid": "sustesting","elo": 1000,'
                                  '"rd": 126.10075385302,"r": 1421.3731832209,'
                                  '"gxe": 34.9,"entryid": "7014174",'
                                  '"rprd": 118.89531340789,"w": "0",'
                                  '"rpsigma": "0","t": "0",'
                                  '"rpr": 1375.663456165,"l": 2}')

        expected_ratings = {
            'w': 0, 'l': 2, 't': 0,
            'elo': 1000,
            'r': 1421.3731832209, 'rd': 126.10075385302,
            'rpr': 1375.663456165, 'rprd': 118.89531340789
            }

        expected = Player('sustesting', expected_ratings)

        player = log_reader.rating_dict_to_model(ratings_dict)

        assert expected == player

    def test_player_with_string_ratings(self):
        ratings_dict = json.loads('{"rptime": 1465462800,"oldelo": "1000",'
                                  '"sigma": "0","formatid": "ou","col1": 2,'
                                  '"username": "sus_testing",'
                                  '"userid": "sustesting","elo": 1000,'
                                  '"rd": 126.10075385302,"r": 1421.3731832209,'
                                  '"gxe": 34.9,"entryid": "7014174",'
                                  '"rprd": "118.89531340789","w": "0",'
                                  '"rpsigma": "0","t": "0",'
                                  '"rpr": 1375.663456165,"l": 2}')

        expected_ratings = {
            'w': 0, 'l': 2, 't': 0,
            'elo': 1000,
            'r': 1421.3731832209, 'rd': 126.10075385302,
            'rpr': 1375.663456165, 'rprd': 118.89531340789
        }

        expected = Player('sustesting', expected_ratings)

        player = log_reader.rating_dict_to_model(ratings_dict)

        assert expected == player

    def test_player_with_missing_ratings(self):
        ratings_dict = json.loads('{"rptime": 1465462800,"oldelo": "1000",'
                                  '"sigma": "0","formatid": "ou","col1": 2,'
                                  '"username": "sus_testing",'
                                  '"userid": "sustesting","elo": 1000,'
                                  '"rd": 126.10075385302,"r": 1421.3731832209,'
                                  '"gxe": 34.9,"entryid": "7014174",'
                                  '"rprd": "118.89531340789","w": "0",'
                                  '"rpsigma": "0","t": "0","l": 2}')

        expected_ratings = {
            'w': 0, 'l': 2, 't': 0,
            'elo': 1000,
            'r': 1421.3731832209, 'rd': 126.10075385302,
            'rpr': None, 'rprd': 118.89531340789
        }

        expected = Player('sustesting', expected_ratings)

        player = log_reader.rating_dict_to_model(ratings_dict)

        assert expected == player


class TestJsonFileLogReader(object):

    def setup_method(self, method):
        context = contexts.Context(pokedex=True, items=True, natures=True,
                                   accessible_formes=True, sanitizer=True,
                                   formats={'test': {'ruleset': []}})
        self.reader = log_reader.JsonFileLogReader(context)

    def test_log_ref_parsing(self):

        # write the test log
        os.makedirs('gsfhsfd/test/2016-05-31')
        json.dump({}, open('gsfhsfd/test/2016-05-31/'
                           'battle-test-8675309.log.json', 'w+'))
        try:
            log_dict = self.reader._parse_log('gsfhsfd/test/2016-05-31/'
                                              'battle-test-8675309.log.json')
            assert 8675309 == log_dict['id']
            assert 2016 == log_dict['date'].year
            assert 5 == log_dict['date'].month
            assert 31 == log_dict['date'].day

        finally:
            shutil.rmtree('gsfhsfd')

    def test_missing_file_raises_parsing_error(self):

        with pytest.raises(log_reader.ParsingError) as e_info:
            self.reader.parse_log('sadgadgadg')

        assert 'sadgadgadg' == e_info.value.log_ref

    def test_malformed_json_raises_parsing_error(self):
        # write the test log
        os.makedirs('vwfqfgs/test/2016-05-31')
        with open('vwfqfgs/test/2016-05-31/battle-test-8675309.log.json',
                  'w+') as f:
            f.write('blah\n')

        try:
            with pytest.raises(log_reader.ParsingError) as e_info:
                self.reader.parse_log('vwfqfgs/test/2016-05-31/'
                                      'battle-test-8675309.log.json')

            assert 'vwfqfgs/test/2016-05-31/' \
                   'battle-test-8675309.log.json' == e_info.value.log_ref
        finally:
            shutil.rmtree('vwfqfgs')

    def test_malformed_filename_raises_parsing_error(self):

        # write the test log
        os.makedirs('pfwwqdb/test/2016-05-31')
        json.dump({}, open('pfwwqdb/test/2016-05-31/asfaf.log.json', 'w+'))

        try:
            with pytest.raises(log_reader.ParsingError) as ei:
                self.reader._parse_log('pfwwqdb/test/2016-05-31/asfaf.log.json')

            assert 'pfwwqdb/test/2016-05-31/asfaf.log.json' == ei.value.log_ref
        finally:
            shutil.rmtree('pfwwqdb')

    def test_datestring_fallback(self):

        # write the test log
        json.dump({}, open('battle-test-8675309.log.json', 'w+'))

        try:
            log_dict = self.reader._parse_log('battle-test-8675309.log.json')

            assert 1970 == log_dict['date'].year
            assert 1 == log_dict['date'].month
            assert 1 == log_dict['date'].day
        finally:
            os.remove('battle-test-8675309.log.json')


class TestLogReader(object):

    def setup_method(self, method):

        context = contexts.get_standard_context()

        self.reader = log_reader.JsonFileLogReader(context)

    def test_read_log(self):
        battle_info, movesets, _ = self.reader.parse_log(
            'tests/test_files/ou/2016-08-04/battle-ou-397190448.log.json')

        expected_teams = [[['crobat'], ['garbodor'], ['muk'], ['nidoking'],
                           ['scolipede'], ['toxicroak'], ],
                          [['chinchou'], ['ferrothorn'],
                           ['gardevoir', 'gardevoirmega'], ['regirock']]]

        actual_teams = []
        for team_sids in battle_info.slots:
            team = []
            for sid in team_sids:
                formes = sorted([forme.species
                                 for forme in movesets[sid].formes])
                team.append(formes)
            team.sort(key=lambda x: str(x))
            actual_teams.append(team)

        assert expected_teams == actual_teams

        expected_players = ['redacted', 'sustesting']

        actual_players = [player.id for player in battle_info.players]

        assert actual_players == expected_players

        assert 1042 == int(battle_info.players[1].rating['elo'])

    def test_ladder_error_falls_back_correctly(self):
        battle_info, movesets, _ = self.reader.parse_log(
            'tests/test_files/doublesubers/2016-04-13/'
            'battle-doublesubers-358755211.log.json')

        expected_players = [Player(pid, dict()) for pid in ('shazaa', 'beeboo')]

        assert expected_players == battle_info.players

    def test_unrecognzied_pokemon_raises_parsing_error(self):

        del self.reader.context.pokedex['scolipede']

        with pytest.raises(log_reader.ParsingError) as e_info:
            self.reader.parse_log('tests/test_files/ou/2016-08-04/'
                                  'battle-ou-397190448.log.json')

        assert 'tests/test_files/ou/2016-08-04/' \
               'battle-ou-397190448.log.json' == e_info.value.log_ref


