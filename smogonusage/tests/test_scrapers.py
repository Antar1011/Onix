"""Tests for scrapers module"""
import json

from smogonusage import scrapers


def test_scrape_formats():
    formats = scrapers.scrape_formats()
    formats_from_file = json.load(open('resources/formats.json'))
    assert(formats == formats_from_file)
    for metagame in formats:
        if metagame['name'] == 'OU':
            ou = metagame
            break
    assert('Uber' in metagame['banlist'])


def test_scrape_battle_formats_data():
    battle_formats = scrapers.scrape_battle_formats_data()
    battle_formats_from_file = json.load(
        open('resources/formats-data.json'))
    assert(battle_formats == battle_formats_from_file)
    assert(battle_formats['arceus']['tier'] == 'Uber')


def test_scrape_battle_pokedex():
    pokedex = scrapers.scrape_battle_pokedex()
    pokedex_from_file = json.load(
        open('resources/pokedex.json'))
    assert(pokedex == pokedex_from_file)
    assert(pokedex['sudowoodo']['types'] == ['Rock'])


def test_scrape_battle_aliases():
    aliases = scrapers.scrape_battle_aliases()
    aliases_from_file = json.load(
        open('resources/aliases.json'))
    assert(aliases == aliases_from_file)
    assert(aliases['jarooda'] == 'Serperior')
