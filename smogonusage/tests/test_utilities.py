"""Tests for utilities module"""
import json

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

    def test_initialize_with_args(self):
        pokedex = json.load(open('resources/pokedex.json'))
        aliases = json.load(open('resources/aliases.json'))
        sanitizer = utilities.Sanitizer(pokedex, aliases)
        input_object = 'Deerling Summer'
        expected = 'deerling'
        assert (expected == sanitizer.sanitize(input_object))
