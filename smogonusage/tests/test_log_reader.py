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
        moveset = Moveset('rayquaza', None, None, None,
                          [], None, None, None)
        expected = Moveset('rayquaza', None, None, None,
                          [], None, None, None)

        assert expected == self.reader._normalize_mega_evolution(moveset, False,
                                                                 True)
        assert 0 == self.reader.devolve_count

    def test_improperly_mega_rayquaza(self):
        moveset = Moveset('rayquazamega', None, None, None,
                          [], None, None, None)
        expected = Moveset('rayquaza', None, None, None,
                          [], None, None, None)

        assert expected == self.reader._normalize_mega_evolution(moveset, False,
                                                                 True)
        assert 1 == self.reader.devolve_count

    def test_improperly_mega_rayquaza_in_hackmons(self):
        moveset = Moveset('rayquazamega', None, None, None,
                          [], None, None, None)
        expected = Moveset('rayquazamega', None, None, None,
                          [], None, None, None)

        assert expected == self.reader._normalize_mega_evolution(moveset, True,
                                                                 True)
        assert 0 == self.reader.devolve_count

    def test_mega_rayquaza_where_allowed(self):
        moveset_1 = Moveset('rayquaza', None, None, None,
                            ['dragonascent'], None, None, None)
        moveset_2 = Moveset('rayquazamega', None, None, None,
                            ['dragonascent'], None, None, None)
        expected = Moveset('rayquazamega', None, None, None,
                           ['dragonascent'], None, None, None)

        for moveset in (moveset_1, moveset_2):
            assert expected == self.reader._normalize_mega_evolution(moveset,
                                                                     False,
                                                                     True)
        assert 0 == self.reader.devolve_count

    def test_mega_rayquaza_where_not_allowed(self):
        moveset_1 = Moveset('rayquaza', None, None, None,
                            ['dragonascent'], None, None, None)
        moveset_2 = Moveset('rayquazamega', None, None, None,
                            ['dragonascent'], None, None, None)
        expected = Moveset('rayquaza', None, None, None,
                           ['dragonascent'], None, None, None)

        for moveset in (moveset_1, moveset_2):
            assert expected == self.reader._normalize_mega_evolution(moveset,
                                                                     False,
                                                                     False)
        assert 1 == self.reader.devolve_count

    def test_non_mega(self):
        moveset = Moveset('gardevoir', None, None,
                          'choicescarf', None, None, None, None)
        expected = Moveset('gardevoir', None, None,
                           'choicescarf', None, None, None, None)

        assert expected == self.reader._normalize_mega_evolution(moveset, False)
        assert 0 == self.reader.devolve_count

    def test_mega(self):
        moveset_1 = Moveset('gardevoir', None, None,
                            'gardevoirite', None, None, None, None)
        moveset_2 = Moveset('gardevoirmega', None, None,
                            'gardevoirite', None, None, None, None)
        expected = Moveset('gardevoirmega', None, None,
                           'gardevoirite', None, None, None, None)

        for moveset in (moveset_1, moveset_2):
            assert expected == self.reader._normalize_mega_evolution(moveset,
                                                                     False)
        assert 0 == self.reader.devolve_count

    def test_improperly_mega(self):
        moveset = Moveset('gardevoirmega', None, None,
                          'choicescarf', None, None, None, None)

        expected = Moveset('gardevoir', None, None,
                           'choicescarf', None, None, None, None)

        assert expected == self.reader._normalize_mega_evolution(moveset, False)
        assert 1 == self.reader.devolve_count

    def test_improperly_mega_in_hackmons(self):
        moveset = Moveset('gardevoirmega', None, None,
                          'choicescarf', None, None, None, None)
        expected = Moveset('gardevoirmega', None, None,
                           'choicescarf', None, None, None, None)

        assert expected == self.reader._normalize_mega_evolution(moveset, True)
        assert 0 == self.reader.devolve_count

    def test_wrong_stone(self):
        moveset = Moveset('gardevoirmega', None, None,
                          'absolite', None, None, None, None)

        expected = Moveset('gardevoir', None, None,
                           'absolite', None, None, None, None)

        assert expected == self.reader._normalize_mega_evolution(moveset, False)
        assert 1 == self.reader.devolve_count

    def test_wrong_stone_in_hackmons(self):
        moveset = Moveset('gardevoirmega', None, None,
                          'absolite', None, None, None, None)
        expected = Moveset('gardevoirmega', None, None,
                           'absolite', None, None, None, None)

        assert expected == self.reader._normalize_mega_evolution(moveset, True)
        assert 0 == self.reader.devolve_count

    def test_no_item(self):
        moveset_1 = Moveset('gardevoir', None, None, None,
                            None, None, None, None)
        moveset_2 = Moveset('gardevoirmega', None, None, None,
                            None, None, None, None)
        expected = Moveset('gardevoir', None, None, None,
                           None, None, None, None)

        for moveset in (moveset_1, moveset_2):
            assert expected == self.reader._normalize_mega_evolution(moveset,
                                                                     False)
        assert 1 == self.reader.devolve_count

    def test_non_mega_forme(self):
        moveset = Moveset('rotomwash', None, None, None,
                          None, None, None, None)
        expected = Moveset('rotomwash', None, None, None,
                          None, None, None, None)
        assert expected == self.reader._normalize_mega_evolution(moveset, False)
        assert 0 == self.reader.devolve_count

    def test_primal_groudon(self):
        moveset_1 = Moveset('groudon', None, None,
                            'redorb', None, None, None, None)
        moveset_2 = Moveset('groudonprimal', None, None,
                            'redorb', None, None, None, None)
        expected = Moveset('groudonprimal', None, None,
                           'redorb', None, None, None, None)
        for moveset in (moveset_1, moveset_2):
            assert expected == self.reader._normalize_mega_evolution(moveset,
                                                                     False)
        assert 0 == self.reader.devolve_count

    def test_primal_kyogre(self):
        moveset_1 = Moveset('kyogre', None, None,
                            'blueorb', None, None, None, None)
        moveset_2 = Moveset('kyogreprimal', None, None,
                            'blueorb', None, None, None, None)
        expected = Moveset('kyogreprimal', None, None,
                           'blueorb', None, None, None, None)
        for moveset in (moveset_1, moveset_2):
            assert expected == self.reader._normalize_mega_evolution(moveset,
                                                                     False)
        assert 0 == self.reader.devolve_count

    def test_non_primal_groudon(self):
        moveset_1 = Moveset('groudon', None, None,
                            None, None, None, None, None)
        moveset_2 = Moveset('groudonprimal', None, None,
                            None, None, None, None, None)
        expected = Moveset('groudon', None, None,
                           None, None, None, None, None)
        for moveset in (moveset_1, moveset_2):
            assert expected == self.reader._normalize_mega_evolution(moveset,
                                                                     False)
        assert 1 == self.reader.devolve_count

    def test_non_primal_kyogre(self):
        moveset_1 = Moveset('kyogre', None, None,
                            None, None, None, None, None)
        moveset_2 = Moveset('kyogreprimal', None, None,
                            None, None, None, None, None)
        expected = Moveset('kyogre', None, None,
                           None, None, None, None, None)
        for moveset in (moveset_1, moveset_2):
            assert expected == self.reader._normalize_mega_evolution(moveset,
                                                                     False)
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
        moveset = Moveset('darmanitanzen', None, None, None, None, None, None,
                          None)
        expected = Moveset('darmanitan', None, None, None, None, None, None,
                          None)
        assert expected == self.reader._normalize_battle_formes(moveset)
        assert 1 == self.reader.battle_forme_undo_count

    def test_meloetta_pirouette(self):
        moveset = Moveset('meloettapirouette', None, None, None, None, None,
                          None, None)
        expected = Moveset('meloetta', None, None, None, None, None, None,
                           None)
        assert expected == self.reader._normalize_battle_formes(moveset)
        assert 1 == self.reader.battle_forme_undo_count

    def test_non_battle_form(self):
        moveset = Moveset('zapdos', None, None, None, None, None, None, None)
        expected = Moveset('zapdos', None, None, None, None, None, None, None)
        assert expected == self.reader._normalize_battle_formes(moveset)
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
        moveset = Moveset('venusaurmega', 'thickfat', None, None, None, None,
                          None, None)
        expected = Moveset('venusaurmega', 'overgrow', None, None, None, None,
                          None, None)
        assert expected == self.reader._normalize_ability(moveset, False)
        assert 1 == self.reader.ability_correct_count

    def test_mega_base_ability(self):
        moveset = Moveset('venusaurmega', 'chlorophyll', None, None, None, None,
                          None, None)
        expected = Moveset('venusaurmega', 'chlorophyll', None, None, None, None,
                           None, None)
        assert expected == self.reader._normalize_ability(moveset, False)
        assert 0 == self.reader.ability_correct_count

    def test_non_mega_wrong_ability(self):
        moveset = Moveset('spiritomb', 'wonderguard', None, None, None, None,
                          None, None)
        expected = Moveset('spiritomb', 'pressure', None, None, None, None,
                           None, None)
        assert expected == self.reader._normalize_ability(moveset, False)
        assert 1 == self.reader.ability_correct_count

    def test_hackmons(self):
        moveset_1 = Moveset('venusaurmega', 'thickfat', None, None, None, None,
                          None, None)
        moveset_2 = Moveset('spiritomb', 'wonderguard', None, None, None, None,
                          None, None)
        for moveset in (moveset_1, moveset_2):
            expected = copy.deepcopy(moveset)
            assert expected == self.reader._normalize_ability(moveset, True)
        assert 0 == self.reader.ability_correct_count



