"""Tests for log readers and related functions"""
import copy
import json

from onix.dto import PokeStats, Moveset, Player
from onix import log_reader
from onix import scrapers
from onix import utilities


class TestMegaEvolutionNormalization(object):

    @classmethod
    def setup_class(cls):
        try:
            cls.pokedex = json.load(open('.psdata/pokedex.json'))
        except IOError:
            cls.pokedex = scrapers.scrape_battle_pokedex()
        try:
            cls.items = json.load(open('.psdata/items.json'))
        except IOError:
            cls.items = scrapers.scrape_battle_items()
        cls.sanitizer = utilities.Sanitizer()

    def setup_method(self, method):
        self.reader = log_reader.JsonFileLogReader(self.sanitizer, self.pokedex,
                                                   self.items)

    def test_non_mega_rayquaza(self):
        species = 'rayquaza'
        expected = 'rayquaza'

        assert expected == self.reader._normalize_mega_evolution(species, None,
                                                                 [], False,
                                                                 True)
        assert 0 == self.reader.devolve_count

    def test_improperly_mega_rayquaza(self):
        species = 'rayquazamega'
        expected = 'rayquaza'

        assert expected == self.reader._normalize_mega_evolution(species, None,
                                                                 [], False,
                                                                 True)
        assert 1 == self.reader.devolve_count

    def test_improperly_mega_rayquaza_in_hackmons(self):
        species = 'rayquazamega'
        expected = 'rayquazamega'

        assert expected == self.reader._normalize_mega_evolution(species, None,
                                                                 [], True,
                                                                 True)
        assert 0 == self.reader.devolve_count

    def test_mega_rayquaza_where_allowed(self):

        expected = 'rayquazamega'

        for species in ('rayquaza', 'rayquazamega'):
            assert expected == self.reader._normalize_mega_evolution(
                species, None, ['dragonascent'], False, True)
        assert 0 == self.reader.devolve_count

    def test_mega_rayquaza_where_not_allowed(self):
        expected = 'rayquaza'

        for species in ('rayquaza', 'rayquazamega'):
            assert expected == self.reader._normalize_mega_evolution(
                species, None, ['dragonascent'], False, False)
        assert 1 == self.reader.devolve_count

    def test_non_mega(self):
        species = 'gardevoir'
        expected = 'gardevoir'

        assert expected == self.reader._normalize_mega_evolution(species,
                                                                 'choicescarf',
                                                                 [], False)
        assert 0 == self.reader.devolve_count

    def test_mega(self):
        expected = 'gardevoirmega'

        for species in ('gardevoir', 'gardevoirmega'):
            assert expected == self.reader._normalize_mega_evolution(
                species, 'gardevoirite', [], False)
        assert 0 == self.reader.devolve_count

    def test_improperly_mega(self):
        species = 'gardevoirmega'
        expected = 'gardevoir'

        assert expected == self.reader._normalize_mega_evolution(species,
                                                                 'choicescarf',
                                                                 [], False)
        assert 1 == self.reader.devolve_count

    def test_improperly_mega_in_hackmons(self):
        species = 'gardevoirmega'
        expected = 'gardevoirmega'

        assert expected == self.reader._normalize_mega_evolution(species,
                                                                 'choicescarf',
                                                                 [], True)
        assert 0 == self.reader.devolve_count

    def test_wrong_stone(self):
        expected = 'gardevoir'

        for species in ('gardevoir', 'gardevoirmega'):
            assert expected == self.reader._normalize_mega_evolution(
                species, 'absolite', [], False)
        assert 1 == self.reader.devolve_count

    def test_wrong_stone_in_hackmons(self):
        species = 'gardevoirmega'
        expected = 'gardevoirmega'

        assert expected == self.reader._normalize_mega_evolution(species,
                                                                 'absolite',
                                                                 [], True)
        assert 0 == self.reader.devolve_count

    def test_no_item(self):
        expected = 'gardevoir'

        for species in ('gardevoir', 'gardevoirmega'):
            assert expected == self.reader._normalize_mega_evolution(species,
                                                                     None, [],
                                                                     False)
        assert 1 == self.reader.devolve_count

    def test_non_mega_forme(self):
        species = 'rotomwash'
        expected = 'rotomwash'

        assert expected == self.reader._normalize_mega_evolution(species,
                                                                 'leftovers',
                                                                 [], False)
        assert 0 == self.reader.devolve_count

    def test_primal_groudon(self):
        expected = 'groudonprimal'

        for species in ('groudon', 'groudonprimal'):
            assert expected == self.reader._normalize_mega_evolution(species,
                                                                     'redorb',
                                                                     [], False)
        assert 0 == self.reader.devolve_count

    def test_primal_kyogre(self):
        expected = 'kyogreprimal'

        for species in ('kyogre', 'kyogreprimal'):
            assert expected == self.reader._normalize_mega_evolution(species,
                                                                     'blueorb',
                                                                     [], False)
        assert 0 == self.reader.devolve_count

    def test_non_primal_groudon(self):
        expected = 'groudon'

        for species in ('groudon', 'groudonprimal'):
            assert expected == self.reader._normalize_mega_evolution(species,
                                                                     'lifeorb',
                                                                     [], False)
        assert 1 == self.reader.devolve_count

    def test_non_primal_kyogre(self):
        expected = 'kyogre'

        for species in ('kyogre', 'kyogreprimal'):
            assert expected == self.reader._normalize_mega_evolution(
                species, 'choicespecs', [], False)
        assert 1 == self.reader.devolve_count


class TestBattleFormeNormalization(object):

    @classmethod
    def setup_class(cls):
        try:
            cls.pokedex = json.load(open('.psdata/pokedex.json'))
        except IOError:
            cls.pokedex = scrapers.scrape_battle_pokedex()
        try:
            cls.items = json.load(open('.psdata/items.json'))
        except IOError:
            cls.items = scrapers.scrape_battle_items()
        cls.sanitizer = utilities.Sanitizer()

    def setup_method(self, method):
        self.reader = log_reader.JsonFileLogReader(self.sanitizer, self.pokedex,
                                                   self.items)

    def test_darmanitan_zen(self):
        species = 'darmanitanzen'
        expected ='darmanitan'

        assert expected == self.reader._normalize_battle_formes(species)
        assert 1 == self.reader.battle_forme_undo_count

    def test_meloetta_pirouette(self):
        species = 'meloettapirouette'
        expected = 'meloetta'

        assert expected == self.reader._normalize_battle_formes(species)
        assert 1 == self.reader.battle_forme_undo_count

    def test_non_battle_form(self):
        species = 'zapdos'
        expected = 'zapdos'

        assert expected == self.reader._normalize_battle_formes(species)
        assert 0 == self.reader.battle_forme_undo_count


class TestAbilityNormalization(object):

    @classmethod
    def setup_class(cls):
        try:
            cls.pokedex = json.load(open('.psdata/pokedex.json'))
        except IOError:
            cls.pokedex = scrapers.scrape_battle_pokedex()
        try:
            cls.items = json.load(open('.psdata/items.json'))
        except IOError:
            cls.items = scrapers.scrape_battle_items()
        cls.sanitizer = utilities.Sanitizer()

    def setup_method(self, method):
        self.reader = log_reader.JsonFileLogReader(self.sanitizer,
                                                   self.pokedex,
                                                   self.items)

    def test_mega_ability(self):
        ability = 'thickfat'
        expected = 'overgrow'
        assert expected == self.reader._normalize_ability('venusaurmega',
                                                          ability, False)
        assert 1 == self.reader.ability_correct_count

    def test_mega_base_ability(self):
        ability = 'chlorophyll'
        expected = 'chlorophyll'

        assert expected == self.reader._normalize_ability('venusaurmega',
                                                          ability, False)
        assert 0 == self.reader.ability_correct_count

    def test_non_mega_wrong_ability(self):
        ability = 'wonderguard'
        expected = 'pressure'

        assert expected == self.reader._normalize_ability('spiritomb',
                                                          ability, False)
        assert 1 == self.reader.ability_correct_count

    def test_hackmons(self):
        species_ability_1 = ('venusaurmega', 'thickfat')
        species_ability_2 = ('spiritomb', 'wonderguard')

        for (species, ability) in (species_ability_1, species_ability_2):
            expected = ability
            assert expected == self.reader._normalize_ability(species,
                                                              ability, True)
        assert 0 == self.reader.ability_correct_count


class TestHiddenPowerNormalization(object):

    @classmethod
    def setup_class(cls):
        try:
            cls.pokedex = json.load(open('.psdata/pokedex.json'))
        except IOError:
            cls.pokedex = scrapers.scrape_battle_pokedex()
        try:
            cls.items = json.load(open('.psdata/items.json'))
        except IOError:
            cls.items = scrapers.scrape_battle_items()
        cls.sanitizer = utilities.Sanitizer()

    def setup_method(self, method):
        self.reader = log_reader.JsonFileLogReader(self.sanitizer,
                                                   self.pokedex,
                                                   self.items)

    def test_correct_hidden_power(self):
        moves = ['earthquake', 'grassknot', 'hiddenpowerfire', 'rapidspin']
        ivs = PokeStats(31, 30, 31, 30, 31, 30)

        expected = ['earthquake', 'grassknot', 'hiddenpowerfire', 'rapidspin']

        assert expected == self.reader._normalize_hidden_power(moves, ivs)
        assert 0 == self.reader.hidden_power_no_type
        assert 0 == self.reader.hidden_power_wrong_type

    def test_no_hidden_power(self):
        moves = ['earthquake', 'grassknot', 'rapidspin']
        ivs = PokeStats(31, 30, 31, 30, 31, 30)

        expected = ['earthquake', 'grassknot', 'rapidspin']

        assert expected == self.reader._normalize_hidden_power(moves, ivs)
        assert 0 == self.reader.hidden_power_no_type
        assert 0 == self.reader.hidden_power_wrong_type

    def test_wrong_hidden_power(self):
        moves = ['earthquake', 'grassknot', 'hiddenpowerice', 'rapidspin']
        ivs = PokeStats(31, 30, 31, 30, 31, 30)

        expected = ['earthquake', 'grassknot', 'hiddenpowerfire', 'rapidspin']

        assert expected == self.reader._normalize_hidden_power(moves, ivs)
        assert 0 == self.reader.hidden_power_no_type
        assert 1 == self.reader.hidden_power_wrong_type

    def test_hidden_power_no_type(self):
        moves = ['earthquake', 'grassknot', 'hiddenpower', 'rapidspin']
        ivs = PokeStats(31, 30, 31, 30, 31, 30)

        expected = ['earthquake', 'grassknot', 'hiddenpowerfire', 'rapidspin']

        assert expected == self.reader._normalize_hidden_power(moves, ivs)
        assert 1 == self.reader.hidden_power_no_type
        assert 0 == self.reader.hidden_power_wrong_type


class TestMovesetParsing(object):

    @classmethod
    def setup_class(cls):
        try:
            cls.pokedex = json.load(open('.psdata/pokedex.json'))
        except IOError:
            cls.pokedex = scrapers.scrape_battle_pokedex()
        try:
            cls.items = json.load(open('.psdata/items.json'))
        except IOError:
            cls.items = scrapers.scrape_battle_items()
        cls.sanitizer = utilities.Sanitizer()

    def setup_method(self, method):
        self.reader = log_reader.JsonFileLogReader(self.sanitizer,
                                                   self.pokedex,
                                                   self.items)

    def test_bare_bones_moveset(self):
        moveset_dict = json.loads('{"name":"Regirock","species":"Regirock",'
                                  '"item":"","ability":"Clear Body",'
                                  '"moves":["ancientpower"],"nature":"",'
                                  '"ivs":{"hp":31,"atk":0,"def":31,"spa":31,'
                                  '"spd":31,"spe":31},"evs":{"hp":0,"atk":0,'
                                  '"def":0,"spa":0,"spd":0,"spe":0}}')

        expected = Moveset('regirock', 'clearbody', 'u', None, ['ancientpower'],
                           PokeStats(301, 205, 436, 136, 236, 136), 100, 255)

        moveset = self.reader._parse_moveset(moveset_dict)

        assert expected == moveset
        assert moveset == self.sanitizer.sanitize(moveset)
        assert 0 == self.reader.devolve_count
        assert 0 == self.reader.battle_forme_undo_count
        assert 0 == self.reader.ability_correct_count

    def test_typical_moveset(self):
        moveset_dict = json.loads('{"name":"Cuddles","species":"ferrothorn",'
                                  '"item":"rockyhelmet","ability":"Iron Barbs",'
                                  '"moves":["stealthrock","leechseed",'
                                  '"gyroball","knockoff"],"nature":"Relaxed",'
                                  '"evs":{"hp":252,"atk":4,"def":252,"spa":0,'
                                  '"spd":0,"spe":0},"gender":"F","ivs":{"hp":31,'
                                  '"atk":31,"def":31,"spa":31,"spd":31,"spe":0},'
                                  '"shiny":true}')

        expected = Moveset('ferrothorn', 'ironbarbs', 'f', 'rockyhelmet',
                           ['gyroball', 'knockoff', 'leechseed', 'stealthrock'],
                           PokeStats(352, 225, 397, 144, 268, 40), 100, 255)

        moveset = self.reader._parse_moveset(moveset_dict)

        assert expected == moveset
        assert moveset == self.sanitizer.sanitize(moveset)
        assert 0 == self.reader.devolve_count
        assert 0 == self.reader.battle_forme_undo_count
        assert 0 == self.reader.ability_correct_count

    def test_standard_mega_evolving_moveset(self):
        moveset_dict = json.loads('{"name":"Gardevoir","species":"Gardevoir",'
                                  '"item":"gardevoirite",'
                                  '"ability":"Trace",'
                                  '"moves":["healingwish"],"nature":"Bold",'
                                  '"evs":{"hp":252,"atk":0,"def":252,"spa":0,'
                                  '"spd":0,"spe":4},"ivs":{"hp":31,"atk":0,'
                                  '"def":31,"spa":31,"spd":31,"spe":31}}')

        expected = Moveset('gardevoirmega', 'trace', 'u', 'gardevoirite',
                           ['healingwish'],
                           PokeStats(340, 157, 251, 366, 306, 237), 100, 255)

        moveset = self.reader._parse_moveset(moveset_dict)

        assert expected == moveset
        assert moveset == self.sanitizer.sanitize(moveset)
        assert 0 == self.reader.devolve_count
        assert 0 == self.reader.battle_forme_undo_count
        assert 0 == self.reader.ability_correct_count

    def test_little_cup(self):
        moveset_dict = json.loads('{"name":"Chinchou","species":"Chinchou",'
                                  '"item":"airballoon","ability":"Volt Absorb",'
                                  '"moves":["charge","discharge","scald",'
                                  '"thunderwave"],"nature":"Modest",'
                                  '"evs":{"hp":4,"atk":0,"def":0,"spa":252,'
                                  '"spd":0,"spe":252},"gender":"M","level":5,'
                                  '"ivs":{"hp":31,"atk":31,"def":31,"spa":31,'
                                  '"spd":31,"spe":31}}')

        expected = Moveset('chinchou', 'voltabsorb', 'm', 'airballoon',
                           ['charge', 'discharge', 'scald', 'thunderwave'],
                           PokeStats(24, 9, 10, 16, 12, 16), 5, 255)

        moveset = self.reader._parse_moveset(moveset_dict)

        assert expected == moveset
        assert moveset == self.sanitizer.sanitize(moveset)
        assert 0 == self.reader.devolve_count
        assert 0 == self.reader.battle_forme_undo_count
        assert 0 == self.reader.ability_correct_count

    def test_improperly_mega_moveset(self):
        moveset_dict = json.loads('{"name":"Gardevoir",'
                                  '"species":"Gardevoirmega",'
                                  '"item":"choicescarf",'
                                  '"ability":"Pixilate",'
                                  '"moves":["healingwish"],"nature":"Bold",'
                                  '"evs":{"hp":252,"atk":0,"def":252,"spa":0,'
                                  '"spd":0,"spe":4},"ivs":{"hp":31,"atk":0,'
                                  '"def":31,"spa":31,"spd":31,"spe":31}}')

        expected = Moveset('gardevoir', 'synchronize', 'u', 'choicescarf',
                           ['healingwish'],
                           PokeStats(340, 121, 251, 286, 266, 197), 100, 255)

        moveset = self.reader._parse_moveset(moveset_dict)

        assert expected == moveset
        assert moveset == self.sanitizer.sanitize(moveset)
        assert 1 == self.reader.devolve_count
        assert 0 == self.reader.battle_forme_undo_count
        assert 1 == self.reader.ability_correct_count


class TestPlayerParsing(object):

    @classmethod
    def setup_class(cls):
        cls.pokedex = {}
        cls.items = {}
        cls.sanitizer = utilities.Sanitizer()

    def setup_method(self, method):
        self.reader = log_reader.JsonFileLogReader(self.sanitizer,
                                                   self.pokedex,
                                                   self.items)
        self.team = [Moveset('gardevoir', 'synchronize', 'u', 'choicescarf',
                             ['healingwish'],
                             PokeStats(340, 121, 251, 286, 266, 197), 100, 255)]

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

        expected = Player('sustesting', utilities.compute_tid(self.team),
                          expected_ratings)

        player = self.reader._parse_player(ratings_dict, self.team)

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

        expected = Player('sustesting', utilities.compute_tid(self.team),
                          expected_ratings)

        player = self.reader._parse_player(ratings_dict, self.team)

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

        expected = Player('sustesting', utilities.compute_tid(self.team),
                          expected_ratings)

        player = self.reader._parse_player(ratings_dict, self.team)

        assert expected == player


