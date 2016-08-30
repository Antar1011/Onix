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


class TestRequire(object):

    def setup_method(self, method):
        self.sc = scs.Scenario(pokedex={'abra': 'Psi'}, quizzibuck=42,
                               duketastrophe=None)

    def test_require_with_no_args(self):
        scs.require(self.sc)

        empty_sc = scs.Scenario()
        scs.require(empty_sc)

    def test_require_for_present_resources(self):
        scs.require(self.sc, 'pokedex', 'quizzibuck')

    def test_require_for_missing_standard_resource(self):
        with pytest.raises(scs.ResourceMissingError):
            scs.require(self.sc, 'formats')

    def test_require_for_missing_nonstandard_resource(self):
        with pytest.raises(scs.ResourceMissingError):
            scs.require(self.sc, 'gawhag')

    def test_require_for_nonstandard_resource_set_to_none(self):
        # still counts as missing
        with pytest.raises(scs.ResourceMissingError):
            scs.require(self.sc, 'duketastrophe')
