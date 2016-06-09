"""Tests for log readers and related functions"""
import copy
import json

from smogonusage.dto import Moveset, PokeStats
from smogonusage import log_reader
from smogonusage import scrapers
from smogonusage import utilities


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

        assert expected == self.reader._parse_moveset(moveset_dict)



