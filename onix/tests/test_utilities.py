"""Tests for utilities module"""
import json
import os
import pytest

from onix.dto import PokeStats, Moveset
from onix import scrapers
from onix import utilities


class TestSanitize(object):

    def setup_method(self, method):
        self.sanitizer = utilities.Sanitizer()

    def test_sanitize_string_1(self):
        input_object = 'Rayquaza-Mega-X'
        expected = 'rayquazamegax'
        assert expected == self.sanitizer.sanitize(input_object)

    def test_sanitize_string_2(self):
        input_object = 'Rotom Wash'
        expected = 'rotomwash'
        assert expected == self.sanitizer.sanitize(input_object)

    def test_sanitize_list(self):
        input_object = ['Giga Drain', 'Power Whip', 'Earthquake', 'Sunny Day']
        expected = ['earthquake', 'gigadrain', 'powerwhip', 'sunnyday']
        assert expected == self.sanitizer.sanitize(input_object)

    def test_sanitize_iterable(self):
        input_object = {'Rock Polish', 'Explosion', 'Rock Blast', 'Hyper Beam'}
        expected = ['explosion', 'hyperbeam', 'rockblast', 'rockpolish']
        assert expected == self.sanitizer.sanitize(input_object)

    def test_sanitize_dict(self):
        input_object = {'itEm': 'Mystic Water', 'level': 100}
        expected = {'itEm': 'mysticwater', 'level': 100}
        assert expected == self.sanitizer.sanitize(input_object)

    def test_sanitize_moveset(self):
        input_object = Moveset('Blastoise-Mega', 'Mega Launcher', 'F',
                               'Blastoisinite', ['Water Spout', 'Aura Sphere',
                                                 'Dragon Pulse', 'Dark Pulse'],
                               PokeStats(361, 189, 276, 405, 268, 192),
                               100, 255)
        expected = Moveset('blastoisemega', 'megalauncher', 'f',
                           'blastoisinite', ['aurasphere', 'darkpulse',
                                             'dragonpulse', 'waterspout'],
                           PokeStats(361, 189, 276, 405, 268, 192),
                           100, 255)
        assert expected == self.sanitizer.sanitize(input_object)

    def test_sanitize_int(self):
        input_object = 3
        with pytest.raises(TypeError):
            self.sanitizer.sanitize(input_object)

    def test_sanitize_None(self):
        input_object = None
        assert self.sanitizer.sanitize(input_object) is None

    def test_sanitize_is_idempotent(self):
        input_object = ['Giga Drain', 'Power Whip', 'Earthquake', 'Sunny Day']
        sanitized = self.sanitizer.sanitize(input_object)
        assert input_object != sanitized
        sanitized_twice = self.sanitizer.sanitize(sanitized)
        assert sanitized == sanitized_twice

    def test_initialize_with_args(self):
        pokedex = json.load(open('.psdata/pokedex.json'))
        aliases = json.load(open('.psdata/aliases.json'))
        sanitizer = utilities.Sanitizer(pokedex, aliases)
        input_object = 'Deerling Summer'
        expected = 'deerling'
        assert expected == sanitizer.sanitize(input_object)

    @pytest.mark.online
    def test_initialize_with_missing_files(self):
        os.remove('.psdata/pokedex.json')
        os.remove('.psdata/aliases.json')
        sanitizer = utilities.Sanitizer()
        input_object = 'Flabebe-blue'
        expected = 'flabebe'
        assert expected == sanitizer.sanitize(input_object)


class TestComputeSid(object):

    def setup_method(self, method):
        self.sanitizer = utilities.Sanitizer()
        self.moveset = Moveset('Blastoise-Mega', 'Mega Launcher', 'F',
                               'Blastoisinite', ['Water Spout', 'Aura Sphere',
                                                 'Dragon Pulse', 'Dark Pulse'],
                               PokeStats(361, 189, 276, 405, 268, 192),
                               100, 255)

    def test_sanitizer_changes_unsanitized_input(self):
        unsanitized_sid = utilities.compute_sid(self.moveset)
        sanitized_sid = utilities.compute_sid(self.moveset, self.sanitizer)
        assert unsanitized_sid != sanitized_sid
        assert sanitized_sid.startswith('blastoisemega-')

    def test_equivalent_sids(self):
        equivalent_moveset = Moveset('Blastoise-Mega', 'Mega Launcher', 'F',
                                     'Blastoisinite',
                                     ['darkpulse', 'dragonpulse', 'waterspout',
                                      'aurasphere'],
                                     PokeStats(spa=405, hp=361, dfn=276,
                                                spd=268, spe=192, atk=189),
                                     100, 255)
        original_sid = utilities.compute_sid(self.moveset, self.sanitizer)
        equivalent_sid = utilities.compute_sid(equivalent_moveset,
                                               self.sanitizer)
        assert original_sid == equivalent_sid

    def test_non_equivalent_sids(self):
        non_equivalent_moveset = Moveset('Blastoise-Mega', 'Mega Launcher', 'F',
                                     'Blastoisinite',
                                     ['darkpulse', 'dragonpulse', 'waterspout',
                                      'aurasphere'],
                                     PokeStats(spa=405, hp=361, dfn=276,
                                               spd=268, spe=192, atk=189),
                                     100, 0)
        original_sid = utilities.compute_sid(self.moveset, self.sanitizer)
        non_equivalent_sid = utilities.compute_sid(non_equivalent_moveset,
                                               self.sanitizer)
        assert original_sid != non_equivalent_sid


class TestComputeTid(object):

    def test_tid_equivalence(self):

        sanitizer = utilities.Sanitizer()

        moveset_1 = Moveset('Blastoise-Mega', 'Mega Launcher', 'F',
                            'Blastoisinite', ['Water Spout', 'Aura Sphere',
                                              'Dragon Pulse', 'Dark Pulse'],
                            PokeStats(361, 189, 276, 405, 268, 192),
                            100, 255)
        moveset_2 = Moveset('gardevoir', 'synchronize', 'u', 'choicescarf',
                            ['healingwish'],
                            PokeStats(340, 121, 251, 286, 266, 197), 100, 255)

        moveset_1a = Moveset('Blastoise-Mega', 'Mega Launcher', 'F',
                             'Blastoisinite', ['Water Spout', 'Aura Sphere',
                                               'Dragon Pulse', 'Dark Pulse'],
                             PokeStats(360, 189, 276, 405, 268, 193),
                             100, 255)

        original_tid = utilities.compute_tid([moveset_1, moveset_2], sanitizer)
        equivalent_tid = utilities.compute_tid([moveset_2, moveset_1],
                                               sanitizer)
        non_equivalent_tid = utilities.compute_tid([moveset_1a, moveset_2],
                                                   sanitizer)

        assert original_tid == equivalent_tid
        assert original_tid != non_equivalent_tid


class TestDictToStats(object):

    def setup_method(self, method):
        self.stats_dict = {'hp': 373, 'atk': 216, 'def': 208, 'spa': 158,
                           'spd': 196, 'spe': 383}

    def test_good_dict(self):
        expected = PokeStats(373, 216, 208, 158, 196, 383)
        assert expected == utilities.stats_dict_to_dto(self.stats_dict)

    def test_missing_key(self):
        del self.stats_dict['atk']
        with pytest.raises(TypeError):
            utilities.stats_dict_to_dto(self.stats_dict)

    def test_extra_key(self):
        self.stats_dict['happiness'] = 255
        with pytest.raises(TypeError):
            utilities.stats_dict_to_dto(self.stats_dict)

    def test_wrong_key_name(self):
        self.stats_dict['hitpoints'] = self.stats_dict.pop('hp')
        with pytest.raises(TypeError):
            utilities.stats_dict_to_dto(self.stats_dict)


class TestCalculateStats(object):

    @classmethod
    def setup_class(cls):
        cls.natures = utilities.load_natures()

    def test_typical_set(self):
        stats = utilities.calculate_stats(PokeStats(125, 120, 90, 170, 100, 95),
                                          self.natures['timid'],
                                          PokeStats(31, 31, 31, 31, 31, 31),
                                          PokeStats(0, 0, 4, 254, 0, 252), 100)
        expected = PokeStats(391, 248, 217, 439, 236, 317)
        assert expected == stats

    def test_lc_set(self):
        stats = utilities.calculate_stats(PokeStats(62, 48, 66, 59, 57, 49),
                                          self.natures['calm'],
                                          PokeStats(31, 0, 31, 31, 31, 31),
                                          PokeStats(180, 0, 0, 124, 60, 124), 5)
        expected = PokeStats(25, 8, 13, 14, 14, 13)
        assert expected == stats

    def test_shedinja(self):
        stats = utilities.calculate_stats(PokeStats(1, 90, 45, 30, 30, 40),
                                          self.natures['relaxed'],
                                          PokeStats(31, 31, 31, 31, 31, 31),
                                          PokeStats(252, 0, 4, 0, 252, 0), 100)
        expected = PokeStats(1, 216, 139, 96, 159, 104)
        assert expected == stats

    def test_neutral_nature(self):
        stats = utilities.calculate_stats(PokeStats(89, 145, 90, 105, 80, 91),
                                          self.natures['docile'],
                                          PokeStats(31, 30, 30, 31, 31, 31),
                                          PokeStats(44, 252, 0, 0, 0, 212), 50)
        expected = PokeStats(170, 196, 110, 125, 100, 138)
        assert expected == stats

    def test_invalid_nature(self):
        with pytest.raises(KeyError):
            utilities.calculate_stats(PokeStats(125, 120, 90, 170, 100, 95),
                                      {'name': 'Timid', 'plus': 'spe'},
                                      PokeStats(31, 31, 31, 31, 31, 31),
                                      PokeStats(0, 0, 4, 254, 0, 252), 100)

    def test_improperly_converted_nature(self):
        with pytest.raises(KeyError):
            utilities.calculate_stats(PokeStats(125, 120, 90, 170, 100, 95),
                                      {'name': 'Hasty', 'plus': 'spe',
                                       'minus': 'def'},
                                      PokeStats(31, 31, 31, 31, 31, 31),
                                      PokeStats(0, 0, 4, 254, 0, 252), 100)


def test_load_natures():
    natures = utilities.load_natures()
    expected = {'name': 'Lonely', 'plus': 'atk', 'minus': 'dfn'}
    assert expected == natures['lonely']


class TestRulesetParsing(object):

    @classmethod
    def setup_class(cls):
        try:
            cls.formats = json.load(open('.psdata/formats.json'))
        except IOError:
            cls.formats = scrapers.scrape_battle_formats()

    def test_ubers(self):
        metagame = 'Ubers'
        expected = ('singles', False, False, False)

        assert expected == utilities.parse_ruleset(self.formats[metagame])

    def test_hackmons(self):
        metagame = 'Balanced Hackmons'
        expected = ('singles', True, False, True)

        assert expected == utilities.parse_ruleset(self.formats[metagame])

    def test_triples(self):
        metagame = 'Smogon Triples'
        expected = ('triples', False, False, True)

        assert expected == utilities.parse_ruleset(self.formats[metagame])

    def test_almost_any_ability(self):
        metagame = 'Almost Any Ability'
        expected = ('singles', False, True, True)

        assert expected == utilities.parse_ruleset(self.formats[metagame])

    def test_anything_goes(self):
        metagame = 'Anything Goes'
        expected = ('singles', False, False, True)

        assert expected == utilities.parse_ruleset(self.formats[metagame])

    def test_doubles_hackmons_cup(self):
        metagame = 'Doubles Hackmons Cup'
        expected = ('doubles', True, False, True)

        assert expected == utilities.parse_ruleset(self.formats[metagame])


class TestDetermineHiddenPowerType(object):

    def test_hex_flawless(self):
        ivs = PokeStats(31, 31, 31, 31, 31, 31)
        assert 'dark' == utilities.determine_hidden_power_type(ivs)

    def test_weird_ivs(self):
        ivs = PokeStats(4, 21, 10, 20, 23, 11)
        assert 'grass' == utilities.determine_hidden_power_type(ivs)

