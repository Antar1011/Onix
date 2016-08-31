"""Tests for log readers and related functions"""
import json
import os
import shutil


from onix.dto import PokeStats, Moveset, Player, Forme
from onix.collection import log_reader
from onix import contexts


class StumpLogReader(log_reader.LogReader):

    def __init__(self, context, metagame):
        super(StumpLogReader,
              self).__init__(metagame, context)

    def _parse_log(self, log_ref):
        pass


class TestHiddenPowerNormalization(object):

    def test_correct_hidden_power(self):
        moves = ['earthquake', 'grassknot', 'hiddenpowerfire', 'rapidspin']
        ivs = PokeStats(31, 30, 31, 30, 31, 30)

        expected = ['earthquake', 'grassknot', 'hiddenpowerfire', 'rapidspin']

        assert expected == log_reader._normalize_hidden_power(moves, ivs)

    def test_no_hidden_power(self):
        moves = ['earthquake', 'grassknot', 'rapidspin']
        ivs = PokeStats(31, 30, 31, 30, 31, 30)

        expected = ['earthquake', 'grassknot', 'rapidspin']

        assert expected == log_reader._normalize_hidden_power(moves, ivs)

    def test_wrong_hidden_power(self):
        moves = ['earthquake', 'grassknot', 'hiddenpowerice', 'rapidspin']
        ivs = PokeStats(31, 30, 31, 30, 31, 30)

        expected = ['earthquake', 'grassknot', 'hiddenpowerfire', 'rapidspin']

        assert expected == log_reader._normalize_hidden_power(moves, ivs)

    def test_hidden_power_no_type(self):
        moves = ['earthquake', 'grassknot', 'hiddenpower', 'rapidspin']
        ivs = PokeStats(31, 30, 31, 30, 31, 30)

        expected = ['earthquake', 'grassknot', 'hiddenpowerfire', 'rapidspin']

        assert expected == log_reader._normalize_hidden_power(moves, ivs)


class TestMovesetParsing(object):
    @classmethod
    def setup_class(cls):
        cls.context = contexts.get_standard_context()

    def test_bare_bones_moveset(self):
        reader = StumpLogReader(self.context, 'ou')
        moveset_dict = json.loads('{"name":"Regirock","species":"Regirock",'
                                  '"item":"","ability":"Clear Body",'
                                  '"moves":["ancientpower"],"nature":"",'
                                  '"ivs":{"hp":31,"atk":0,"def":31,"spa":31,'
                                  '"spd":31,"spe":31},"evs":{"hp":0,"atk":0,'
                                  '"def":0,"spa":0,"spd":0,"spe":0}}')

        expected = Moveset([Forme('regirock', 'clearbody',
                                  PokeStats(301, 205, 436, 136, 236, 136))],
                           'u', None, ['ancientpower'], 100, 255)

        moveset = reader._parse_moveset(moveset_dict)

        assert expected == moveset
        assert moveset == self.context.sanitizer.sanitize(moveset)

    def test_typical_moveset(self):
        reader = StumpLogReader(self.context, 'ou')
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

        moveset = reader._parse_moveset(moveset_dict)

        assert expected == moveset
        assert moveset == self.context.sanitizer.sanitize(moveset)

    def test_standard_mega_evolving_moveset(self):
        reader = StumpLogReader(self.context, 'ou')
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

        moveset = reader._parse_moveset(moveset_dict)

        assert expected == moveset
        assert moveset == self.context.sanitizer.sanitize(moveset)

    def test_little_cup(self):
        reader = StumpLogReader(self.context, 'lc')
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

        moveset = reader._parse_moveset(moveset_dict)

        assert expected == moveset
        assert moveset == self.context.sanitizer.sanitize(moveset)

    def test_improperly_mega_moveset(self):
        reader = StumpLogReader(self.context, 'ou')
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

        moveset = reader._parse_moveset(moveset_dict)

        assert expected == moveset
        assert moveset == self.context.sanitizer.sanitize(moveset)


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

        player = log_reader.rating_dict_to_dto(ratings_dict)

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

        player = log_reader.rating_dict_to_dto(ratings_dict)

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

        player = log_reader.rating_dict_to_dto(ratings_dict)

        assert expected == player


class TestJsonFileLogReader(object):

    def setup_method(self, method):
        context = contexts.Context(pokedex=True, items=True, natures=True,
                                   accessible_formes=True, sanitizer=True,
                                   formats={'test': {'ruleset': []}})
        self.reader = log_reader.JsonFileLogReader('test', context, 'gsfhsfd')

    def test_log_ref_parsing(self):

        # write the test log
        os.makedirs('gsfhsfd/test/2016-05-31')
        json.dump({}, open('gsfhsfd/test/2016-05-31/'
                           'battle-test-8675309.log.json', 'w+'))
        try:
            log_dict = self.reader._parse_log('2016-05-31/'
                                              'battle-test-8675309.log.json')
            assert 8675309 == log_dict['id']
            assert 2016 == log_dict['date'].year
            assert 5 == log_dict['date'].month
            assert 31 == log_dict['date'].day

        finally:
            shutil.rmtree('gsfhsfd')


class TestLogReader(object):

    def setup_method(self, method):

        context = contexts.get_standard_context()

        self.reader = log_reader.JsonFileLogReader('ou', context,
                                                   'onix/tests/test_files')

    def test_read_log(self):
        battle_info, movesets, _ = self.reader.parse_log(
            '2016-08-04/battle-ou-397190448.log.json')

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



