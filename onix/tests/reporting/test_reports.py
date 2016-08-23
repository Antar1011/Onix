"""Tests for the reports module"""
import json

import pytest

from onix import scrapers
from onix.reporting import dao
from onix.reporting import reports


class MockReportingDao(dao.ReportingDAO):

    def get_usage_by_species(self, month, metagame, baseline=1630.0):
        if metagame == 'ou':
            return {'landorustherian': 6178.08,
                    'heatran': 6065.64,
                    'garchomp': 5645.13,
                    'latios': 5706.78,
                    'scizor,scizormega': 3589.16,
                    'scizor': 3179.75,
                    'charizard,charizardmegay': 3847.24,
                    'charizard,charizardmegax': 3964.92,
                    'gastrodon': 443.41,
                    'charizard': 291.33,
                    'gastrodoneast': 169.59,
                    None: 123.45}

    def get_number_of_battles(self, month, metagame):
        if metagame == 'ou':
            return 5000


class TestSpeciesLookup(object):

    def setup_method(self, method):
        try:
            pokedex = json.load(open('.psdata/pokedex.json'))
        except IOError:
            pokedex = scrapers.scrape_battle_pokedex()
        try:
            aliases = json.load(open('.psdata/aliases.json'))
        except IOError:
            aliases = scrapers.scrape_battle_aliases()

        self.lookup = reports.SpeciesLookup(pokedex, aliases)

    def test_easy_mapping(self):
        assert 'Feraligatr' == self.lookup.lookup('feraligatr')

    def test_mega_forme(self):
        assert 'Lopunny-Mega' == self.lookup.lookup('lopunny,lopunnymega')

    def test_mega_forme_when_megas_are_not_counted_separately(self):
        assert 'Lopunny' == self.lookup.lookup('lopunny,lopunnymega',
                                               count_megas_separately=False)

    def test_nonexistent_pokemon(self):
        with pytest.raises(KeyError):
            self.lookup.lookup('sgsafgargva')

    def test_appearance_only_forme(self):
        assert 'Gastrodon' == self.lookup.lookup('gastrodoneast')

    def test_hackmon(self):
        assert 'Aegislash-Blade' == self.lookup.lookup('aegislashblade')


class TestGenerateUsageStats(object):

    def setup_method(self, method):
        self.dao = MockReportingDao()

        try:
            pokedex = json.load(open('.psdata/pokedex.json'))
        except IOError:
            pokedex = scrapers.scrape_battle_pokedex()

        self.lookup = reports.SpeciesLookup(pokedex)

    def test_generate_ou_report(self):

        expected = "Total battles: 5000\n" \
                   "Avg. weight / team: 0.653408\n" \
                   "+ ---- + ------------------------- + --------- +\n" \
                   "| Rank | Species                   | Usage %   |\n" \
                   "+ ---- + ------------------------- + --------- +\n" \
                   "|    1 | Landorus-Therian          |  94.5516% |\n" \
                   "|    2 | Heatran                   |  92.8308% |\n" \
                   "|    3 | Latios                    |  87.3387% |\n" \
                   "|    4 | Garchomp                  |  86.3952% |\n" \
                   "|    5 | Charizard-Mega-X          |  60.6806% |\n" \
                   "|    6 | Charizard-Mega-Y          |  58.8796% |\n" \
                   "|    7 | Scizor-Mega               |  54.9298% |\n" \
                   "|    8 | Scizor                    |  48.6641% |\n" \
                   "|    9 | Gastrodon                 |   9.3815% |\n" \
                   "|   10 | Charizard                 |   4.4586% |\n" \
                   "+ ---- + ------------------------- + --------- +\n"

        assert expected == reports.generate_usage_stats(dao,
                                                        self.lookup,
                                                        '2016-08', 'ou',
                                                        baseline=1695.0)

