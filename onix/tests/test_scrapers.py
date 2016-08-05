"""Tests for scrapers module"""
import json
import os
import shutil

import pytest

from onix import scrapers


@pytest.mark.online
def test_scrape_battle_formats_data():
    battle_formats = scrapers.scrape_battle_formats_data()
    battle_formats_from_file = json.load(
        open('.psdata/formats-data.json'))
    assert(battle_formats == battle_formats_from_file)
    assert(battle_formats['arceus']['tier'] == 'Uber')


@pytest.mark.online
def test_scrape_battle_pokedex():
    pokedex = scrapers.scrape_battle_pokedex()
    pokedex_from_file = json.load(open('.psdata/pokedex.json'))
    assert(pokedex == pokedex_from_file)
    assert(pokedex['sudowoodo']['types'] == ['Rock'])


class TestScrapeBattlePokedex(object):

    def setup_method(self, method):
        self.pokedex = json.load(open('.psdata/pokedex.json'))

    def test_megas_baseable(self):
        assert 'Swampert' == self.pokedex['swampertmega']['baseSpecies']

    def test_baseable_pokemon_baseable(self):
        assert 'Shaymin' == self.pokedex['shayminsky']['baseSpecies']

    def test_not_baseable_pokemon_not_baseable(self):
        assert 'baseSpecies' not in self.pokedex['rotomheat']


@pytest.mark.online
def test_scrape_battle_aliases():
    aliases = scrapers.scrape_battle_aliases()
    aliases_from_file = json.load(
        open('.psdata/aliases.json'))
    assert(aliases == aliases_from_file)
    assert(aliases['jarooda'] == 'Serperior')


@pytest.mark.online
def test_scrape_battle_items():
    items = scrapers.scrape_battle_items()
    items_from_file = json.load(
        open('.psdata/items.json'))
    assert(items == items_from_file)
    assert(items['kingsrock']['name'] == "King's Rock")


@pytest.mark.online
def test_scrape_battle_movedex():
    moves = scrapers.scrape_battle_movedex()
    moves_from_file = json.load(
        open('.psdata/moves.json'))
    assert(moves == moves_from_file)
    assert(moves['amnesia'] == 'Amnesia')

@pytest.mark.online
def test_make_directory():
    os.rename('.psdata', '.bkp')

    try:
        test_scrape_battle_items()
    finally:
        shutil.rmtree('.psdata', ignore_errors=True)
        os.rename('.bkp', '.psdata')


@pytest.mark.online
def test_scrape_formats():
    formats = scrapers.scrape_formats()
    formats_from_file = json.load(open('.psdata/formats.json'))
    assert formats == formats_from_file
    assert 'Swagger Clause' in formats['OU']['ruleset']
    assert 'Swagger Clause' in formats['NU']['ruleset']