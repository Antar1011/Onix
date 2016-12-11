"""Tests for the reports module"""
import pytest

from onix.reporting import dao
from onix.reporting import reports
from onix.utilities import sanitize_string


class MockReportingDao(dao.ReportingDAO):

    def get_usage_by_species(self, month, metagame, species_lookup,
                             baseline=1630., min_turns=3,
                             remove_duplicates=True):

        if remove_duplicates:
            if metagame == 'ou' and month == '2016-08' and baseline == 1695.:
                return [('Landorus-Therian', 6178.08),
                        ('Heatran', 6065.64),
                        ('Latios', 5706.78),
                        ('Garchomp', 5645.13),
                        ('Charizard-Mega-X', 3964.92),
                        ('Charizard-Mega-Y', 3847.24),
                        ('Scizor-Mega', 3589.16),
                        ('Scizor', 3179.75),
                        ('Gastrodon', 613.0),
                        ('Charizard', 291.33),
                        ('-froobat', 1.72)]
            elif metagame == 'superlongspeciesname':
                return [('Iamtheverymodelofamodernmajorgeneral', 100.)]
            else:
                return []
        else:
            return [('Gardevoir', 3159.7242049098722)]

    def get_number_of_battles(self, month, metagame, min_turns=3):
        if min_turns == 3:
            return 5000
        else:
            return 10000

    def get_total_weight(self, month, metagame, baseline=1630., min_turns=3):
        if metagame == 'ou' and month == '2016-08' and baseline == 1695.:
            return 39206.2 / 6
        elif metagame == 'superlongspeciesname':
            return 100.
        else:
            return 0.

    def get_abilities(self, month, metagame, species_lookup, baseline=1630.,
                      min_turns=3):
        return {'Greninja': [('battlebond', 1344.34),
                             ('protean', 874.18),
                             ('torrent', 3.16)]}

    def get_items(self, month, metagame, species_lookup, baseline=1630.,
                  min_turns=3):
        return {'Mimikyu': [('redcard', 4136.4),
                            ('lifeorb', 2122.1),
                            ('leftovers', 763.5),
                            ('rockyhelmet', 641.4),
                            ('sitrusberry', 515.2),
                            (None, 438.6),
                            ('choicescarf', 104.2),
                            ('choiceband', 32.5)]}

    def get_moves(self, month, metagame, species_lookup, baseline=1630.,
                  min_turns=3):
        return {'Gardevoir': [('moonblast', 2910.180752876876),
                              ('psyshock', 2146.663963315812),
                              ('focusblast', 1121.349013116779),
                              ('shadowball', 922.8393445795723),
                              ('trick', 863.8870974895382),
                              ('psychic', 813.8666072038525),
                              ('healingwish', 614.9632960497555),
                              ('calmmind', 584.9185568367136),
                              ('energyball', 484.34216343120784),
                              ('thunderbolt', 405.1195104937233),
                              ('willowisp', 296.3178343124676),
                              ('wish', 187.86064774058318),
                              ('drainingkiss', 148.9529732337462),
                              ('substitute', 148.06187168614923),
                              ('destinybond', 142.72945386488473),
                              ('healbell', 117.78457197311003),
                              ('thunderwave', 104.35814117154588),
                              ('hiddenpowerfire', 98.27482279622076),
                              ('dazzlinggleam', 76.3011726620313),
                              ('reflect', 74.64398191862318)]}


@pytest.fixture(scope='module')
def empty_report():
    return ' Total battles: 5000\n'\
           ' Avg. weight / team: 0.000000\n'\
           ' + ---- + ------------------------- + --------- +\n'\
           ' | Rank | Species                   | Usage %   |\n'\
           ' + ---- + ------------------------- + --------- +\n'\
           ' + ---- + ------------------------- + --------- +\n'


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
                       'gastrodoneast': 'Gastrodon',
                       'quilava': 'Quilava'}

    def test_raise_error_for_unkown_species(self):
        with pytest.raises(KeyError):
            reports.generate_usage_stats(self.dao,
                                         self.lookup,
                                         '2016-08', 'ou',
                                         baseline=1695.0,
                                         unknown_species_handling='raise')

        with pytest.raises(KeyError):
            reports.generate_usage_stats(self.dao,
                                         self.lookup,
                                         '2016-08', 'ou',
                                         baseline=1695.0)

    def test_raise_error_if_invalid_error_handling_kwarg(self):
        with pytest.raises(ValueError):
            reports.generate_usage_stats(self.dao,
                                         self.lookup,
                                         '2016-08', 'ou',
                                         baseline=1695.0,
                                         unknown_species_handling='afadgadg')

    def test_no_data(self, empty_report):

        assert empty_report == reports.generate_usage_stats(self.dao,
                                                            self.lookup,
                                                            '2016-08', 'adgadgad',
                                                            baseline=1695.0)

        assert empty_report == reports.generate_usage_stats(self.dao,
                                                            self.lookup,
                                                            '2016-09', 'ou',
                                                            baseline=1695.0)

        assert empty_report == reports.generate_usage_stats(self.dao,
                                                            self.lookup,
                                                            '2016-08', 'ou')

    def test_generate_ou_report_guess_unknown_species(self):

        expected = " Total battles: 5000\n" \
                   " Avg. weight / team: 0.653437\n" \
                   " + ---- + ------------------------- + --------- +\n" \
                   " | Rank | Species                   | Usage %   |\n" \
                   " + ---- + ------------------------- + --------- +\n" \
                   " |    1 | Landorus-Therian          |  94.5475% |\n" \
                   " |    2 | Heatran                   |  92.8267% |\n" \
                   " |    3 | Latios                    |  87.3349% |\n" \
                   " |    4 | Garchomp                  |  86.3914% |\n" \
                   " |    5 | Charizard-Mega-X          |  60.6780% |\n" \
                   " |    6 | Charizard-Mega-Y          |  58.8770% |\n" \
                   " |    7 | Scizor-Mega               |  54.9274% |\n" \
                   " |    8 | Scizor                    |  48.6619% |\n" \
                   " |    9 | Gastrodon                 |   9.3812% |\n" \
                   " |   10 | Charizard                 |   4.4584% |\n" \
                   " |   11 | Froobat                   |   0.0263% |\n" \
                   " + ---- + ------------------------- + --------- +\n"

        output = reports.generate_usage_stats(self.dao,
                                              self.lookup,
                                              '2016-08', 'ou',
                                              baseline=1695.0,
                                              unknown_species_handling='guess')
        assert expected == output

    def test_long_species_report(self):

        exp = " Total battles: 5000\n" \
              " Avg. weight / team: 0.010000\n" \
              " + ---- + ------------------------------------ + --------- +\n" \
              " | Rank | Species                              | Usage %   |\n" \
              " + ---- + ------------------------------------ + --------- +\n" \
              " |    1 | Iamtheverymodelofamodernmajorgeneral | 100.0000% |\n" \
              " + ---- + ------------------------------------ + --------- +\n"

        output = reports.generate_usage_stats(self.dao,
                                              self.lookup,
                                              '2016-08',
                                              'superlongspeciesname',
                                              unknown_species_handling='guess')

        assert exp == output

    def test_no_min_turns(self):
        exp = ' Total battles: 10000\n'\
              ' Avg. weight / team: 0.000000\n'\
              ' + ---- + ------------------------- + --------- +\n'\
              ' | Rank | Species                   | Usage %   |\n'\
              ' + ---- + ------------------------- + --------- +\n'\
              ' + ---- + ------------------------- + --------- +\n'

        output = reports.generate_usage_stats(self.dao,
                                              self.lookup,
                                              '2016-08',
                                              'fdjbjkkf',
                                              min_turns=0)

        assert exp == output


class TestGenerateAbilitiesReport(object):

    def setup_method(self, method):
        self.dao = MockReportingDao()
        self.abilities = {'battlebond': {'name': 'Battle Bond'},
                          'protean': {'name': 'Protean'},
                          'torrent': {'name': 'Torrent'}}
        self.species_lookup = {'greninja': 'Greninja'}
        '''Greninja and Greninja-Ash are almost certainly going to be counted
        separately. I don't care for these purposes'''

    def test_generate_report(self):
        expected = ' | Abilities                                        |\n'\
                   ' | Battle Bond 60.510%                              |\n'\
                   ' | Protean 39.348%                                  |\n'\
                   ' | Other 0.142%                                     |\n'\
                   ' + ------------------------------------------------ +\n'

        output = reports.generate_abilities_reports(self.dao, self.abilities,
                                                   self.species_lookup,
                                                   '2016-11', 'gen7ou',
                                                   min_lines=1)

        assert {'Greninja'} == output.keys()

        assert expected == output['Greninja']

    def test_raise_error_for_unkown_ability(self):

        del self.abilities['battlebond']

        with pytest.raises(KeyError):
            reports.generate_abilities_reports(self.dao, self.abilities,
                                              self.species_lookup,
                                              '2016-11', 'gen7ou')


class TestGenerateItemsReport(object):

    def setup_method(self, method):
        self.dao = MockReportingDao()
        self.items = {'choiceband': {'name': 'Choice Band'},
                      'choicescarf': {'name': 'Choice Scarf'},
                      'leftovers': {'name': 'Leftovers'},
                      'lifeorb': {'name': 'Life Orb'},
                      'redcard': {'name': 'Red Card'},
                      'rockyhelmet': {'name': 'Rocky Helmet'},
                      'sitrusberry': {'name': 'Sitrus Berry'}}
        self.species_lookup = {'mimikyu': 'Mimikyu'}

    def test_generate_report(self):
        expected = ' | Items                                            |\n'\
                   ' | Red Card 47.252%                                 |\n'\
                   ' | Life Orb 24.242%                                 |\n'\
                   ' | Leftovers 8.722%                                 |\n' \
                   ' | Rocky Helmet 7.327%                              |\n' \
                   ' | Sitrus Berry 5.885%                              |\n' \
                   ' | No Item 5.010%                                   |\n' \
                   ' | Other 1.562%                                     |\n' \
                   ' + ------------------------------------------------ +\n'

        output = reports.generate_items_reports(self.dao, self.items,
                                                self.species_lookup,
                                                '2016-11', 'gen7pokebankou',
                                                min_lines=1)

        assert {'Mimikyu'} == output.keys()

        assert expected == output['Mimikyu']

    def test_raise_error_for_unkown_item(self):

        del self.items['redcard']

        with pytest.raises(KeyError):
            reports.generate_items_reports(self.dao, self.items,
                                           self.species_lookup,
                                           '2016-11', 'gen7pokebankou')

    def test_unknown_rare_item_raises_no_error(self):

        del self.items['choicescarf']

        reports.generate_items_reports(self.dao, self.items,
                                       self.species_lookup,
                                       '2016-11', 'gen7pokebankou')


class TestGenerateMovesReport(object):

    def setup_method(self, method):
        self.dao = MockReportingDao()

        self.moves = {sanitize_string(move): {'name': move}
                      for move in ['Calm Mind',
                                   'Dazzling Gleam',
                                   'Destiny Bond',
                                   'Draining Kiss',
                                   'Energy Ball',
                                   'Focus Blast',
                                   'Heal Bell',
                                   'Healing Wish',
                                   'Hidden Power Fire',
                                   'Moonblast',
                                   'Psychic',
                                   'Psyshock',
                                   'Reflect',
                                   'Shadow Ball',
                                   'Substitute',
                                   'Thunder Wave',
                                   'Thunderbolt',
                                   'Trick',
                                   'Will-O-Wisp',
                                   'Wish']}

        self.species_lookup = {'gardevoir': 'Gardevoir'}

    def test_generate_report(self):
        expected = ' | Moves                                            |\n'\
                   ' | Moonblast 92.102%                                |\n'\
                   ' | Psyshock 67.938%                                 |\n' \
                   ' | Focus Blast 35.489%                              |\n' \
                   ' | Shadow Ball 29.206%                              |\n' \
                   ' | Trick 27.341%                                    |\n' \
                   ' | Psychic 25.758%                                  |\n' \
                   ' | Healing Wish 19.463%                             |\n' \
                   ' | Calm Mind 18.512%                                |\n' \
                   ' | Energy Ball 15.329%                              |\n' \
                   ' | Thunderbolt 12.821%                              |\n' \
                   ' | Will-O-Wisp  9.378%                              |\n' \
                   ' | Wish  5.945%                                     |\n' \
                   ' | Draining Kiss  4.714%                            |\n' \
                   ' | Substitute  4.686%                               |\n' \
                   ' | Destiny Bond  4.517%                             |\n' \
                   ' | Heal Bell  3.728%                                |\n' \
                   ' | Thunder Wave  3.303%                             |\n' \
                   ' | Other 19.771%                                    |\n' \
                   ' + ------------------------------------------------ +\n'

        totals = self.dao.get_usage_by_species('2016-10', 'uu',
                                               self.species_lookup,
                                               remove_duplicates=False)
        output = reports.generate_moves_reports(self.dao, totals, self.moves,
                                                self.species_lookup,
                                                '2016-10', 'uu',
                                                min_lines=1)

        assert {'Gardevoir'} == output.keys()

        assert expected == output['Gardevoir']

    def test_raise_error_for_unkown_move(self):

        del self.moves['trick']

        totals = self.dao.get_usage_by_species('2016-10', 'uu',
                                               self.species_lookup,
                                               remove_duplicates=False)
        with pytest.raises(KeyError):
            reports.generate_moves_reports(self.dao, totals,
                                           self.moves,
                                           self.species_lookup,
                                           '2016-10', 'uu')

    def test_unknown_rare_move_raises_no_error(self):

        del self.moves['reflect']

        totals = self.dao.get_usage_by_species('2016-10', 'uu',
                                               self.species_lookup,
                                               remove_duplicates=False)
        reports.generate_moves_reports(self.dao, totals, self.moves,
                                       self.species_lookup,
                                       '2016-10', 'uu',
                                       min_lines=1)
