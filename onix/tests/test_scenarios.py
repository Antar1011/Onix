"""Tests for scenarios module"""
import json
import shutil
import os

import pytest

from onix import scrapers
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


@pytest.mark.online
class TestGetStandardScenario(object):

    def test_get_local_standard_scenario(self):

        try:
            scs.get_standard_scenario()  # scrape once if not already scraped

            mock_pokedex = {'wooper': dict(entry='Water Fish')}
            json.dump(mock_pokedex, open('.psdata/pokedex.json', 'w+'))

            sc = scs.get_standard_scenario()

            assert mock_pokedex == sc.pokedex

        finally:
            scrapers.scrape_battle_pokedex()

    def test_scrape_all(self):

        os.rename('.psdata', '.bkp')

        try:
            sc = scs.get_standard_scenario()
            assert 'Water' == sc.moves['surf']['type']

        finally:
            shutil.rmtree('.psdata', ignore_errors=True)
            os.rename('.bkp', '.psdata')

    def test_force_scrape_all(self):

        try:
            mock_aliases = {'megacharizard': 'pidgey'}
            json.dump(mock_aliases, open('.psdata/aliases.json', 'w+'))

            # test the test
            assert 'pidgey' == json.load(
                open('.psdata/aliases.json'))['megacharizard']

            sc = scs.get_standard_scenario(force_refresh=True)
            assert 'Charizard-Mega-Y' == sc.aliases['megacharizard']

        finally:
            scrapers.scrape_battle_aliases()




