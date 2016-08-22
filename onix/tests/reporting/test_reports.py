"""Tests for the reports module"""

import pytest

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


class TestLookupSpecies(object):

    def test_easy_mapping(self):
        assert 'Feraligatr' == reports.lookup_species('feraligatr')

    def test_mega_forme(self):
        assert 'Lopunny-Mega' == reports.lookup_species('lopunny,lopunnymega')

    def test_mega_forme_when_megas_are_not_counted_separately(self):
        assert 'Lopunny' == reports.lookup_species('lopunny,lopunnymega',
                                                   count_megas_separately=False)

    def test_nonexistent_pokemon(self):
        with pytest.raises('ValueError'):
            reports.lookup_species('sgsafgargva')

    def test_appearance_only_forme(self):
        assert 'Gastrodon' == reports.lookup_species('gastrodoneast')

    def test_hackmon(self):
        assert 'Aegislash-Blade' == reports.lookup_species('aegislashblade')


class TestGenerateUsageStats(object):

    def setup_method(self, method):
        self.dao = MockReportingDao()

    def test_generate_ou_report(self):

        expected = "Total battles: 5000" \
                   "Avg. weight / team: 0.653408" \
                   "+ ---- + ------------------------- + --------- +" \
                   "| Rank | Species                   | Usage %   |" \
                   "+ ---- + ------------------------- + --------- +" \
                   "|    1 | Landorus-Therian          |  94.5516% |" \
                   "|    2 | Heatran                   |  92.8308% |" \
                   "|    3 | Latios                    |  87.3387% |" \
                   "|    4 | Garchomp                  |  86.3952% |" \
                   "|    5 | Charizard-Mega-X          |  60.6806% |" \
                   "|    6 | Charizard-Mega-Y          |  58.8796% |" \
                   "|    7 | Scizor-Mega               |  54.9298% |" \
                   "|    8 | Scizor                    |  48.6641% |" \
                   "|    9 | Gastrodon                 |   9.3815% |" \
                   "|   10 | Charizard                 |   4.4586% |" \
                   "+ ---- + ------------------------- + --------- +"

        assert expected == reports.generate_usage_stats(dao,
                                                        reports.lookup_species,
                                                        '2016-08', 'ou',
                                                        baseline=1695.0)

