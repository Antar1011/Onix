"""Tests for utilities module"""
from smogonusage import utilities


class SanitizeTests(object):

    def setup_method(self):
        self.sanitizer = utilities.Sanitizer()

    def test_sanitize_string_1(self):
        input_object = 'Rayquaza-Mega-X'
        expected = 'rayquazamegax'
        assert (expected == self.sanitizer.sanitize(input_object))

    def test_sanitize_string_2(self):
        input_object = 'Floette White'
        expected = 'floettewhite'
        assert (expected == self.sanitizer.sanitize(input_object))

    def test_sanitize_list(self):
        input_object = ['Giga Drain', 'Power Whip', 'Earthquake', 'Sunny Day']
        expected = ['earthquake', 'gigadrain', 'powerwhip', 'sunnyday']
        assert (expected == self.sanitizer.sanitize(input_object))

    def test_sanitize_iterable(self):
        input_object = {'Rock Polish', 'Explosion', 'Rock Blast', 'Hyper Beam'}
        expected = ['explosion', 'hyperbeam', 'rockblast', 'rockpolish']
        assert (expected == self.sanitizer.sanitize(input_object))
