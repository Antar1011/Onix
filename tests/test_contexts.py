"""Tests for scenarios module"""
import datetime
import json
import shutil
import os

import pytest

from onix import scrapers
from onix import contexts as cxs


class TestContext(object):

    def test_empty_context(self):
        cx = cxs.Context()

        cx.formats is None # accessing one of the standard resources is fine

        with pytest.raises(AttributeError):
            cx.jfjfgjgjf  # trying to access a non-std resource raises an error

    def test_context_with_standard_attributes(self):

        cx = cxs.Context(pokedex={'squirtle': 'Tiny Turtle'},
                         species_lookup={'squirtle': 'Squirtle'})

        assert 'Tiny Turtle' == cx.pokedex['squirtle']
        assert 'Squirtle' == cx.species_lookup['squirtle']

    def test_context_with_nonstandard_attributes(self):

        cx = cxs.Context(agadgda=6)

        assert 6 == cx.agadgda


class TestRequire(object):

    def setup_method(self, method):
        self.cx = cxs.Context(pokedex={'abra': 'Psi'}, quizzibuck=42,
                              duketastrophe=None)

    def test_require_with_no_args(self):
        cxs.require(self.cx)

        empty_cx = cxs.Context()
        cxs.require(empty_cx)

    def test_require_for_present_resources(self):
        cxs.require(self.cx, 'pokedex', 'quizzibuck')

    def test_require_for_missing_standard_resource(self):
        with pytest.raises(cxs.ResourceMissingError):
            cxs.require(self.cx, 'formats')

    def test_require_for_missing_nonstandard_resource(self):
        with pytest.raises(cxs.ResourceMissingError):
            cxs.require(self.cx, 'gawhag')

    def test_require_for_nonstandard_resource_set_to_none(self):
        # still counts as missing
        with pytest.raises(cxs.ResourceMissingError):
            cxs.require(self.cx, 'duketastrophe')


@pytest.mark.online
class TestGetStandardContext(object):

    def test_get_local_standard_context(self):

        try:
            cxs.get_standard_context()  # scrape once if not already scraped

            mock_pokedex = {'wooper': dict(entry='Water Fish')}
            json.dump(mock_pokedex, open('.psdata/pokedex.json', 'w+'))

            cx = cxs.get_standard_context()

            assert mock_pokedex == cx.pokedex

        finally:
            scrapers.scrape_battle_pokedex()

    def test_scrape_all(self):

        os.rename('.psdata', '.bkp')

        try:
            cx = cxs.get_standard_context()
            assert 'Water' == cx.moves['surf']['type']

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

            cx = cxs.get_standard_context(force_refresh=True)
            assert 'Charizard-Mega-Y' == cx.aliases['megacharizard']

        finally:
            scrapers.scrape_battle_aliases()


@pytest.mark.online
def test_get_historical_context():

    timestamp = datetime.datetime(2014, 8, 1, 0, 0)  # Aegi was banned 8/2
    commit = '78da28dc5bdcf0ef00176cdc74585ddfbb0d2366'

    shutil.rmtree('.psdata/{}'.format(commit), ignore_errors=True)

    cx = cxs.get_historical_context(timestamp)

    formats_data_from_file = json.load(
        open('.psdata/{}/formats_data.json'.format(commit)))

    assert cx.formats_data == formats_data_from_file

    assert cx.formats_data['aegislash']['tier'] == 'OU'
    assert 'swampertite' not in cx.items.keys()




