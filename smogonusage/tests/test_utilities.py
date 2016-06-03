"""Tests for utilities module"""
import json
import os
import pytest

from smogonusage import utilities


class TestSanitize(object):

    def setup_method(self, method):
        self.sanitizer = utilities.Sanitizer()

    def test_sanitize_string_1(self):
        input_object = 'Rayquaza-Mega-X'
        expected = 'rayquazamegax'
        assert (expected == self.sanitizer.sanitize(input_object))

    def test_sanitize_string_2(self):
        input_object = 'Rotom Wash'
        expected = 'rotomwash'
        assert (expected == self.sanitizer.sanitize(input_object))

    def test_sanitize_list(self):
        input_object = ['Giga Drain', 'Power Whip', 'Earthquake', 'Sunny Day']
        expected = ['earthquake', 'gigadrain', 'powerwhip', 'sunnyday']
        assert (expected == self.sanitizer.sanitize(input_object))

    def test_sanitize_iterable(self):
        input_object = {'Rock Polish', 'Explosion', 'Rock Blast', 'Hyper Beam'}
        expected = ['explosion', 'hyperbeam', 'rockblast', 'rockpolish']
        assert (expected == self.sanitizer.sanitize(input_object))

    def test_sanitize_dict(self):
        input_object = {'itEm': 'Mystic Water', 'level': 100}
        expected = {'itEm': 'mysticwater', 'level': 100}
        assert (expected == self.sanitizer.sanitize(input_object))

    def test_sanitize_int(self):
        input_object = 3
        with pytest.raises(TypeError):
            self.sanitizer.sanitize(input_object)

    def test_sanitize_None(self):
        input_object = None
        assert (self.sanitizer.sanitize(input_object) is None)

    def test_initialize_with_args(self):
        pokedex = json.load(open('resources/pokedex.json'))
        aliases = json.load(open('resources/aliases.json'))
        sanitizer = utilities.Sanitizer(pokedex, aliases)
        input_object = 'Deerling Summer'
        expected = 'deerling'
        assert (expected == sanitizer.sanitize(input_object))

    @pytest.mark.onlinetest
    def test_initialize_with_missing_files(self):
        os.remove('resources/pokedex.json')
        os.remove('resources/aliases.json')
        sanitizer = utilities.Sanitizer()
        input_object = 'Arceus-bug'
        expected = 'arceusbug'
        assert (expected == sanitizer.sanitize(input_object))
