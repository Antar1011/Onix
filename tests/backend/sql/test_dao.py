"""Tests for SQL DAO implementations, using in-memory SQLite"""
import pytest
import sqlalchemy as sa

from onix.backend.sql import schema
from onix.backend.sql import dao

'''
===data summary===
movesets:
  00 - Articuno
  01 - Basculin
  02 - Basculin-Blue-Striped
  03 - Camerupt
  04 - Camerupt-Mega

teams:
  00 - Articuno & Basculin & Camerupt-Mega
  01 - Three identical Articunos
  02 - Basculin & two Basculin-Blue-Striped
  03 - Camerupt

battles:
  1 - (outside of date range)
  2 - Alice (rating 3000, team 00) vs. Bob (rating 1630, team 01)
  3 - Bob (rating 1630, team 01) vs. Eve (rating 0, team 02)
  4 - (wrong tier)
  5 - Alice (rating 3000, team 00) vs. Eve (rating 0, team 00)
  6 - (early forfeit+)
  7 - Eve (rating 1630, team 03) vs. Bob (rating 1630, team 01)
  8 - (outside of date range*)

So the expected values are:

# of battles: 4

total weight:
    unweighted: 8
    default: 4
    3000 baseline: 1

usage counts:
    unweighted:
        Articuno - 6
        Basculin - 4
        Camerupt - 1
        Camerupt-Mega - 3
    default:
        Articuno - 3.5
        Basculin - 2
        Camerupt - 0.5
        Camerupt-Mega - 2
    3000 baseline:
        Articuno - 2
        Basculin - 2
        Camerupt - 0
        Camerupt-Mega - 2

+Battle 6 is for testing the omission of the minimum-turn filter, so Battle 6
is:
    Delia (high rating, team 02) vs. Bob (rating 1500, team 03)

and thus, the expected values are:

    total weight:
        unweighted: 10

    usage counts:
        unweighted:
            Articuno - 7
            Basculin - 5
            Camerupt - 1
            Camerupt-Mega - 3

        TODO: pickup here

*Battle 8 is for testing missing-rating-handling and high-deviation weighting
policy, so Battle 8 is:
    Charley (rating unknown, team 03) vs. Bob (high rating, team 01)

and thus, the expected values are:

    total weight:
        1500 baseline: 1.5
        1501 baseline: 1

    usage counts:
        1500 baseline:
            Articuno - 1
            Camerupt - 0.5
        1501 baseline:
            Articuno - 1
'''


@pytest.fixture()
def species_lookup():
    # Camerupt intentionally omitted
    return {'articuno': 'Articuno',
            'basculin': 'Basculin',
            'basculinbluestriped': 'Basculin',
            'camerupt,cameruptmega': 'Camerupt-Mega'}


@pytest.fixture()
def engine():
    return sa.create_engine('sqlite:///')


@pytest.fixture()
def initialize_db(engine):
    schema.create_tables(engine)

    with engine.connect() as conn:
        conn.execute('INSERT INTO movesets (id) VALUES '
                     '("00"), '
                     '("01"), '
                     '("02"), '
                     '("03"), '
                     '("04")')
        conn.execute('INSERT INTO formes (id, species, ability) VALUES '
                     '("00", "articuno", "snowcloak"), '
                     '("01", "basculin", "reckless"), '
                     '("02", "basculinbluestriped", "moldbreaker"), '
                     '("03", "cameruptmega", "sheerforce"), '
                     '("04", "camerupt", "angerpoint")')
        conn.execute('INSERT INTO moveset_forme (sid, fid, prime) VALUES '
                     '("00", "00", 1), '
                     '("01", "01", 1), '
                     '("02", "02", 1), '
                     '("03", "04", 1), '
                     '("04", "03", 0), '
                     '("04", "04", 1)')
        conn.execute('INSERT INTO teams (tid, idx, sid) VALUES '
                     '("00", 0, "00"), '
                     '("00", 1, "01"), '
                     '("00", 2, "04"), '
                     '("01", 0, "00"), '
                     '("01", 1, "00"), '
                     '("01", 2, "00"), '
                     '("02", 0, "01"), '
                     '("02", 1, "02"), '
                     '("02", 2, "02"), '
                     '("03", 3, "03")')
        conn.execute('INSERT INTO battle_infos '
                     '(id, format, date, turns, end_type) VALUES '
                     '(1, "anythinggoes", "2016-07-19", 46, "normal"), '
                     '(2, "anythinggoes", "2016-08-01", 13, "forfeit"), '
                     '(3, "anythinggoes", "2016-08-07", 26, "forfeit"), '
                     '(4, "ubers", "2016-08-10", 7, "normal"), '
                     '(5, "anythinggoes", "2016-08-13", 38, "normal"), '
                     '(6, "anythinggoes", "2016-08-15", 2, "forfeit"), '
                     '(7, "anythinggoes", "2016-08-31", 68, "normal"), '
                     '(8, "anythinggoes", "2016-09-15", 38, "forfeit")')
        conn.execute('INSERT INTO battle_players '
                     '(bid, side, pid, tid, rpr, rprd) VALUES '
                     '(1, 1, "charley", "03", 1500., 130.), '
                     '(1, 2, "delia", "02", 5000., 25.), '
                     '(2, 1, "alice", "00", 3000., 27.), '
                     '(2, 2, "bob", "01", 1630., 75.), '
                     '(3, 1, "bob", "01", 1630., 63.), '
                     '(3, 2, "eve", "02", 0., 37.), '
                     '(4, 1, "delia", "02", 5000., 25.), '
                     '(4, 2, "eve", "02", 100., 32.), '
                     '(5, 1, "alice", "00", 3000., 25.), '
                     '(5, 2, "eve", "00", 0., 28.), '
                     '(6, 1, "delia", "02", 5000., 25.), '
                     '(6, 2, "bob", "01", 1500., 48.), '
                     '(7, 1, "eve", "03", 1630., 25.), '
                     '(7, 2, "bob", "01", 1630., 33.), '
                     '(8, 1, "charley", "03", NULL, NULL), '
                     '(8, 2, "bob", "01", 2760., 28.)')


@pytest.fixture()
def reporting_dao(engine):
    with engine.connect() as conn:
        yield dao.ReportingDAO(conn)


@pytest.mark.usefixtures('initialize_db')
class TestGetNumberOfBattles(object):

    def test_get_number_of_battles(self, reporting_dao):
        result = reporting_dao.get_number_of_battles('201608', 'anythinggoes',
                                                     min_turns=3)
        assert 4 == result

    def test_no_battles(self, reporting_dao):
        result = reporting_dao.get_number_of_battles('201608', 'agwegafg',
                                                     min_turns=3)
        assert 0 == result

    def test_no_min_turn(self, reporting_dao):
        result = reporting_dao.get_number_of_battles('201608', 'anythinggoes',
                                                     min_turns=0)
        assert 5 == result


@pytest.mark.usefixtures('initialize_db')
class TestGetTotalWeight(object):

    def test_default_baseline(self, reporting_dao):
        result = reporting_dao.get_total_weight('201608', 'anythinggoes',
                                                min_turns=3)
        assert 4. == round(result, 6)

    def test_unweighted(self, reporting_dao):
        result = reporting_dao.get_total_weight('201608', 'anythinggoes',
                                                baseline=0., min_turns=3)
        assert 8. == round(result, 6)

    def test_custom_baseline(self, reporting_dao):
        result = reporting_dao.get_total_weight('201608', 'anythinggoes',
                                                baseline=3000., min_turns=3)
        assert 1. == round(result, 6)

    def test_no_battles(self, reporting_dao):
        result = reporting_dao.get_total_weight('201608', 'vwrvaad',
                                                baseline=3000., min_turns=3)
        assert 0. == result

    def test_missing_ratings(self, reporting_dao):
        result = reporting_dao.get_total_weight('201609', 'anythinggoes',
                                                baseline=1500., min_turns=3)
        assert 1.5 == round(result, 6)

    def test_high_deviation_weighting_policy(self, reporting_dao):
        result = reporting_dao.get_total_weight('201609', 'anythinggoes',
                                                baseline=1501., min_turns=3)
        assert 1. == round(result, 6)

    def test_no_min_turn(self, reporting_dao):
        result = reporting_dao.get_total_weight('201608', 'anythinggoes',
                                                baseline=0., min_turns=0)
        assert 10 == round(result, 6)


@pytest.mark.usefixtures('initialize_db')
class TestGetUsageBySpecies(object):

    def test_default_baseline(self, reporting_dao, species_lookup):
        expected_keys = ('Articuno', 'Basculin', 'Camerupt-Mega', '-camerupt')
        expected_values = (3.5, 2., 2., 0.5)
        result = reporting_dao.get_usage_by_species('201608', 'anythinggoes',
                                                    species_lookup, min_turns=3)
        unzipped = list(zip(*result))
        assert expected_keys == unzipped[0]
        assert all([e == round(a, 6)
                    for e, a in zip(expected_values, unzipped[1])])

    def test_unweighted(self, reporting_dao, species_lookup):
        expected_keys = ('Articuno', 'Basculin', 'Camerupt-Mega', '-camerupt')
        expected_values = (6., 4., 3., 1.)
        result = reporting_dao.get_usage_by_species('201608', 'anythinggoes',
                                                    species_lookup, baseline=0,
                                                    min_turns=3)
        unzipped = list(zip(*result))
        assert expected_keys == unzipped[0]
        assert all([e == round(a, 6)
                   for e, a in zip(expected_values, unzipped[1])])

    def test_custom_baseline(self, reporting_dao, species_lookup):
        expected_keys = ('Articuno', 'Basculin', 'Camerupt-Mega', '-camerupt')
        expected_values = (1., 1., 1., 0.)
        result = reporting_dao.get_usage_by_species('201608', 'anythinggoes',
                                                    species_lookup,
                                                    baseline=3000., min_turns=3)
        unzipped = list(zip(*result))
        assert expected_keys == unzipped[0]
        assert all([e == round(a, 6)
                    for e, a in zip(expected_values, unzipped[1])])

    def test_no_battles(self, reporting_dao, species_lookup):
        result = reporting_dao.get_usage_by_species('201503', 'anythinggoes',
                                                    species_lookup, min_turns=3)
        assert [] == result

    def test_missing_ratings(self, reporting_dao, species_lookup):
        expected_keys = ('Articuno', '-camerupt')
        expected_values = (1., 0.5)
        result = reporting_dao.get_usage_by_species('201609', 'anythinggoes',
                                                    species_lookup,
                                                    baseline=1500., min_turns=3)
        unzipped = list(zip(*result))
        assert expected_keys == unzipped[0]
        assert all([e == round(a, 6)
                    for e, a in zip(expected_values, unzipped[1])])

    def test_high_deviation_weighting_policy(self, reporting_dao,
                                             species_lookup):
        expected_keys = ('Articuno', '-camerupt')
        expected_values = (1., 0.)
        result = reporting_dao.get_usage_by_species('201609', 'anythinggoes',
                                                    species_lookup,
                                                    baseline=1501., min_turns=3)
        unzipped = list(zip(*result))
        assert expected_keys == unzipped[0]
        assert all([e == round(a, 6)
                    for e, a in zip(expected_values, unzipped[1])])

    def test_no_min_turn(self, reporting_dao, species_lookup):
        expected_keys = ('Articuno', 'Basculin', 'Camerupt-Mega', '-camerupt')
        expected_values = (7., 5., 3., 1.)
        result = reporting_dao.get_usage_by_species('201608', 'anythinggoes',
                                                    species_lookup, baseline=0,
                                                    min_turns=0)
        unzipped = list(zip(*result))
        assert expected_keys == unzipped[0]
        assert all([e == round(a, 6)
                    for e, a in zip(expected_values, unzipped[1])])


@pytest.mark.usefixtures('initialize_db')
class TestGetAbilities(object):

    def test_unweighted(self, reporting_dao, species_lookup):

        expected_species = {'Articuno', 'Basculin', 'Camerupt-Mega',
                            '-camerupt'}

        expected_abilities = ('reckless', 'moldbreaker')  # for Basculin

        '''RS appears on team 00 and 02, one time each, and those teams show up
        in four battles. BS appears on team 02, which only appears once, but
        it's there twice'''
        expected_values = (4, 2)

        result = reporting_dao.get_abilities('201608', 'anythinggoes',
                                             species_lookup, baseline=0)
        assert expected_species == result.keys()

        unzipped = list(zip(*result['Basculin']))
        assert expected_abilities == unzipped[0]
        assert all([e == round(a, 6)
                    for e, a in zip(expected_values, unzipped[1])])

    def test_only_pulls_prime_ability(self, reporting_dao, species_lookup):
        expected_abilities = ('angerpoint',)

        expected_values = (2.,)

        result = reporting_dao.get_abilities('201608', 'anythinggoes',
                                             species_lookup)

        unzipped = list(zip(*result['Camerupt-Mega']))
        assert expected_abilities == unzipped[0]
        assert all([e == round(a, 6)
                    for e, a in zip(expected_values, unzipped[1])])


