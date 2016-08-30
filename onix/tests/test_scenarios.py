"""Tests for scenarios module"""
import pytest

from onix import scenarios as scs


class TestScenario(object):

    def test_empty_scenario(self):
        sc = scs.Scenario()

        sc.formats is None # accessing one of the standard resources is fine

        with pytest.raises(AttributeError):
            sc.jfjfgjgjf  # trying to access a non-std resource raises an error

    def test_scenario_with_standard_attributes(self):

        sc = scs.Scenario(pokedex={'squirtle': 'Tiny Turtle'},
                          species_lookup={'squirtle': 'Squirtle'})

        assert 'Tiny Turtle' == sc.pokedex['squirtle']
        assert 'Squirtle' == sc.species_lookup['squirtle']

    def test_scenario_with_nonstandard_attributes(self):

        sd = scs.Scenario(agadgda=6)

        assert 6 == sd.agadgda
