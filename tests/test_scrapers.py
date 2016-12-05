"""Tests for scrapers module"""
import datetime
import json
import os
import shutil

import pytest

from onix import scrapers


@pytest.mark.online
def test_get_commit_from_timestamp():
    expected = 'f4e01502cc36c90dd3150d845ef6406554a77a0e'
    timestamp = datetime.datetime(2016, 12, 5, 5, 0)
    assert expected == scrapers.get_commit_from_timestamp(timestamp)


@pytest.mark.online
def test_scrape_battle_formats_data():
    commit = '5c14138b54dddf8bc034433eaef950a1c6eaf734'  # late Gen 6
    battle_formats = scrapers.scrape_battle_formats_data(commit=commit)
    battle_formats_from_file = json.load(
        open('.psdata/{}/formats_data.json'.format(commit)))
    assert(battle_formats == battle_formats_from_file)
    assert(battle_formats['arceus']['tier'] == 'Uber')


@pytest.mark.online
class TestScrapeBattlePokedex(object):

    def setup_class(cls):
        cls.pokedex = scrapers.scrape_battle_pokedex()

    def test_load_from_file(self):
        pokedex_from_file = json.load(open('.psdata/pokedex.json'))
        assert self.pokedex == pokedex_from_file

    def test_type_data(self):
        assert self.pokedex['sudowoodo']['types'] == ['Rock']

    def test_megas_baseable(self):
        assert 'Swampert' == self.pokedex['swampertmega']['baseSpecies']

    def test_baseable_pokemon_baseable(self):
        assert 'Castform' == self.pokedex['castformsunny']['baseSpecies']

    def test_not_baseable_pokemon_not_baseable(self):
        assert 'baseSpecies' not in self.pokedex['rotomheat']

    def test_primals_not_baseable(self):
        # primals start as primals and can't go back
        assert 'baseSpecies' not in self.pokedex['kyogreprimal']


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
    assert(moves['amnesia']['name'] == 'Amnesia')


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
    commit = '5c14138b54dddf8bc034433eaef950a1c6eaf734'  # late Gen 6
    formats = scrapers.scrape_formats(commit=commit)
    formats_from_file = json.load(
        open('.psdata/{}/formats.json'.format(commit)))
    assert formats == formats_from_file
    assert 'Swagger Clause' in formats['ou']['ruleset']
    assert 'Swagger Clause' in formats['nu']['ruleset']


@pytest.mark.online
class TestCommitSelection(object):

    def test_scrape_old_pokedex(self):
        commit = '5c14138b54dddf8bc034433eaef950a1c6eaf734'  # late Gen 6
        pokedex = scrapers.scrape_battle_pokedex(commit=commit)
        pokedex_from_file = json.load(
            open('.psdata/{}/pokedex.json'.format(commit)))
        assert pokedex == pokedex_from_file
        assert 'mimikyu' not in pokedex.keys()

    def test_scrape_old_aliases(self):
        commit = '5c14138b54dddf8bc034433eaef950a1c6eaf734'  # late Gen 6
        aliases = scrapers.scrape_battle_aliases(commit=commit)
        aliases_from_file = json.load(
            open('.psdata/{}/aliases.json'.format(commit)))
        assert aliases == aliases_from_file
        assert 'zyc' not in aliases.keys()

    def test_scrape_old_items(self):
        commit = 'bf2c64525b0920a096c91978ddb192990189c7bd'  # pre-ORAS
        items = scrapers.scrape_battle_items(commit=commit)
        items_from_file = json.load(
            open('.psdata/{}/items.json'.format(commit)))
        assert items == items_from_file
        assert 'beedrillite' not in items.keys()

    def test_scrape_old_moves(self):
        commit = '5c14138b54dddf8bc034433eaef950a1c6eaf734'  # late Gen 6
        moves = scrapers.scrape_battle_movedex(commit=commit)
        moves_from_file = json.load(
            open('.psdata/{}/moves.json'.format(commit)))
        assert moves == moves_from_file
        assert 'leafage' not in moves.keys()

    def test_scrape_new_formats_schema(self):
        formats = scrapers.scrape_formats()
        formats_from_file = json.load(open('.psdata/formats.json'))
        assert formats == formats_from_file
