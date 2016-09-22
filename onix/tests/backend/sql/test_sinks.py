"""Tests for SQL sink implementations, using in-memory SQLite"""
import json
import pytest

from onix.dto import Moveset, Forme, PokeStats
from onix import scrapers
from onix import utilities
from onix.backend.sql import sinks

@pytest.fixture()
def sanitizer():
    try:
        pokedex = json.load(open('.psdata/pokedex.json'))
    except IOError:
        pokedex = scrapers.scrape_battle_pokedex()

    try:
        aliases = json.load(open('.psdata/aliases.json'))
    except IOError:
        aliases = scrapers.scrape_battle_aliases()

    return utilities.Sanitizer(pokedex, aliases)


class TestComputeTid(object):

    @staticmethod
    @pytest.fixture()
    def set_1():
        return Moveset([Forme('Blastoise-Mega', 'Mega Launcher',
                              PokeStats(361, 189, 276, 405, 268, 192)),
                        Forme('Blastoise', 'Rain Dish',
                              PokeStats(361, 153, 236, 295, 248, 192))],
                       'F', 'Blastoisinite',
                       ['Water Spout', 'Aura Sphere', 'Dragon Pulse',
                        'Dark Pulse'], 100, 255)

    @staticmethod
    @pytest.fixture()
    def set_2():
        return Moveset([Forme('gardevoir', 'synchronize',
                              PokeStats(340, 121, 251, 286, 266, 197))],
                       'u', 'choicescarf', ['healingwish'], 100, 255)

    @staticmethod
    @pytest.fixture()
    def original_tid(sanitizer, set_1, set_2):
        return sinks.compute_tid([set_1, set_2], sanitizer)

    def test_tid_equivalence(self, sanitizer, set_1, set_2, original_tid):

        set_1a = Moveset([Forme('Blastoise-Mega', 'Mega Launcher',
                                PokeStats(360, 189, 276, 405, 268, 193)),
                          Forme('Blastoise', 'Rain Dish',
                                PokeStats(360, 153, 236, 295, 248, 193))],
                         'F', 'Blastoisinite',
                         ['Water Spout', 'Aura Sphere', 'Dragon Pulse',
                          'Dark Pulse'], 100, 255)

        equivalent_tid = sinks.compute_tid([set_2, set_1], sanitizer)
        non_equivalent_tid = sinks.compute_tid([set_1a, set_2],  sanitizer)

        assert original_tid == equivalent_tid
        assert original_tid != non_equivalent_tid

    def test_compute_by_sids(self, sanitizer, set_1, set_2, original_tid):

        sid_1 = utilities.compute_sid(set_1, sanitizer)
        sid_2 = utilities.compute_sid(set_2, sanitizer)

        tid_by_sid = sinks.compute_tid([sid_1, sid_2])
        reversed = sinks.compute_tid([sid_2, sid_1])

        assert original_tid == tid_by_sid
        assert original_tid == reversed

    def test_invalid_type(self):

        with pytest.raises(TypeError):
            sinks.compute_tid([3, 6, 2])
