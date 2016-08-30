"""Tests for the metrics module"""

from onix import metrics


class TestVictoryChance(object):

    def test_elo(self):
        """Glicko formula should reduce to Elo if d1=d2=0
        Using http://bzstats.strayer.de/bzinfo/elo/ to test against"""
        assert .76 == round(metrics.victory_chance(1200, 0, 1000, 0), 2)

    def test_elo_lower_rating_first(self):
        assert .24 == round(metrics.victory_chance(1000, 0, 1200, 0), 2)

    def test_elo_all_that_matters_is_rating_difference(self):

        expected = metrics.victory_chance(1432, 0, 1164, 0)

        assert expected == metrics.victory_chance(1768, 0, 1500, 0)

    def test_equal_r(self):
        """When R values are the same, odds are always 50/50"""
        assert .5 == metrics.victory_chance(1328, 48, 1328, 126)


def test_gxe():
    """Value pulled from PS ladder"""
    assert 83.3 == round(metrics.gxe(1803, 31), 1)

