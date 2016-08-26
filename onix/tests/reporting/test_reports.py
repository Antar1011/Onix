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
                    'froobat': 1.72,
                    None: 123.45}

    def get_number_of_battles(self, month, metagame):
        if metagame == 'ou':
            return 5000


class TestGenerateUsageStats(object):

    def setup_method(self, method):
        self.dao = MockReportingDao()

        self.lookup = {'landorustherian': 'Landorus-Therian',
                       'heatran': 'Heatran',
                       'latios': 'Latios',
                       'scizor': 'Scizor',
                       'scizor,scizormega': 'Scizor-Mega',
                       'charizard': 'Charizard',
                       'charizard,charizardmegax': 'Charizard-Mega-X',
                       'charizard,charizardmegay': 'Charizard-Mega-Y',
                       'gastrodon': 'Gastrodon',
                       'gastrodoneast': 'Gastrodon_East'}

    def test_raise_error_for_unkown_species(self):
        with pytest.raises(KeyError):
            reports.generate_usage_stats(dao,
                                         self.lookup,
                                         '2016-08', 'ou',
                                         baseline=1695.0,
                                         unkown_species_handling='raise')

    def test_raise_error_if_invalid_error_handling_kwarg(self):
        with pytest.raises(ValueError):
            reports.generate_usage_stats(dao,
                                         self.lookup,
                                         '2016-08', 'ou',
                                         baseline=1695.0,
                                         unkown_species_handling='afadgadg')

    def test_dao_calls(self):
        with pytest.raises(TypeError) as e:
            reports.generate_usage_stats(dao,
                                         self.lookup,
                                         '2016-08', 'adgadgad')
        assert str(e.value).startswith("'NoneType' object")

    def test_generate_ou_report_guess_unknown_species(self):

        expected = "Total battles: 5000\n" \
                   "Avg. weight / team: 0.653408\n" \
                   "+ ---- + ------------------------- + --------- +\n" \
                   "| Rank | Species                   | Usage %   |\n" \
                   "+ ---- + ------------------------- + --------- +\n" \
                   "|    1 | Landorus-Therian          |  94.5475% |\n" \
                   "|    2 | Heatran                   |  92.8267% |\n" \
                   "|    3 | Latios                    |  87.3349% |\n" \
                   "|    4 | Garchomp                  |  86.3919% |\n" \
                   "|    5 | Charizard-Mega-X          |  60.6780% |\n" \
                   "|    6 | Charizard-Mega-Y          |  58.8770% |\n" \
                   "|    7 | Scizor-Mega               |  54.9274% |\n" \
                   "|    8 | Scizor                    |  48.6619% |\n" \
                   "|    9 | Gastrodon                 |   9.3812% |\n" \
                   "|   10 | Charizard                 |   4.4586% |\n" \
                   "|   11 | Froobat                   |   0.0263% |\n" \
                   "+ ---- + ------------------------- + --------- +\n"

        output = reports.generate_usage_stats(dao,
                                              self.lookup,
                                              '2016-08', 'ou',
                                              baseline=1695.0,
                                              unknown_species_handling='guess')
        assert expected == output

