"""Tests for the log_processor module"""
import datetime
import glob
import json
import shutil
import os

import pytest

from collections import defaultdict

from onix import contexts
from onix import utilities
from onix.collection import log_reader as lr
from onix.collection import log_processor as lp
from onix.collection import sinks
from onix.scripts import log_generator as lg


class StumpMovesetSink(sinks.MovesetSink):
    """MovesetSink implementation that just adds the SIDs to a set"""

    def __init__(self):
        self.sids = set()

    def store_movesets(self, movesets):
        start_size = len(self.sids)

        self.sids.update(movesets.keys())

        return len(self.sids) - start_size


class StumpBattleInfoSink(sinks.BattleInfoSink):
    """BattleInfoSink that just keeps track of sets of unique IDs"""

    def __init__(self):
        self.pids = set()
        self.tids = set()
        self.battles = defaultdict(set)

    def store_battle_info(self, battle_info):
        start_sizes = {'players': len(self.pids),
                       'teams': len(self.tids),
                       'battles': len(self.battles)}

        self.pids.update([player.id for player in battle_info.players])
        self.tids.update([utilities.compute_tid(team)
                          for team in battle_info.slots])
        self.battles[battle_info.format].add(battle_info.id)

        return {'players': len(self.pids) - start_sizes['players'],
                'teams': len(self.tids) - start_sizes['teams'],
                'battles': len(self.battles) - start_sizes['battles']}


def test_processor_without_sinks():
    """Should still work, should still parse the logs, even though nothing
    actually gets persisted"""
    context = contexts.get_standard_context()

    players = [lg.generate_player(username)[0]
               for username in ['Alice', 'Bob']]

    moveset, _ = lg.generate_pokemon('articuno', context)

    log = lg.generate_log(players, [[moveset], [moveset]])

    try:
        json.dump(log, open('battle-randombattle-134341313.log.json', 'w+'))
        p = lp.LogProcessor(None, None, None)
        result = p.process_logs('battle-randombattle-134341313.log.json',
                                ref_type='file')
        assert 1 == result

    finally:
        os.remove('battle-randombattle-134341313.log.json')


def test_process_single_log():
    context = contexts.get_standard_context()

    players = [lg.generate_player(username, formatid='ou')[0]
               for username in ['Alice', 'Bob']]

    movesets = [lg.generate_pokemon(species, context)[0]
                for species in ['alakazammega',
                                'bisharp',
                                'cacturne',
                                'delphox',
                                'electabuzz',
                                'flygon',
                                'gogoat',
                                'hariyama',
                                'infernape',
                                'jumpluff',
                                'bisharp']]

    teams = [movesets[:6], movesets[5:]]

    log = lg.generate_log(players, teams)

    try:
        json.dump(log, open('battle-ou-195629539.log.json', 'w+'))
        p = lp.LogProcessor(StumpMovesetSink(), StumpBattleInfoSink(), None)

        result = p.process_logs('battle-ou-195629539.log.json', ref_type='file')

        assert 1 == result

        assert 11 == len(p.moveset_sink.sids)
        assert 2 == len(p.battle_info_sink.pids)
        assert 2 == len(p.battle_info_sink.tids)
        assert {'ou'} == set(p.battle_info_sink.battles.keys())
        assert 1 == len(p.battle_info_sink.battles['ou'])

    finally:
        os.remove('battle-ou-195629539.log.json')


class TestProcessMultipleLogs(object):

    def setup_method(self, method):
        self.context = contexts.get_standard_context()

        players = [lg.generate_player(username, formatid='uu')[0]
                   for username in ('Alice', 'Bob')]
        players += [lg.generate_player(username, formatid='ou')[0]
                    for username in ('Charley', 'Delia')]
        players.append(lg.generate_player('Eve', formatid='uu')[0])

        movesets = [lg.generate_pokemon(species, self.context)[0]
                    for species in ('alakazammega',
                                    'bisharp',
                                    'cacturne',
                                    'delphox',
                                    'electabuzz',
                                    'flygon',
                                    'gogoat',
                                    'hariyama',
                                    'infernape',
                                    'jumpluff',
                                    'kangaskhan',
                                    'lucario',
                                    'bisharp',
                                    'lucariomega')]

        teams = [movesets[:6],
                 movesets[6:12],
                 [movesets[i] for i in (1, 12, 3, 4, 5, 6)],
                 [movesets[i] for i in (3, 5, 6, 8, 9, 13)]]

        logs = [lg.generate_log(players[:2], teams[:2]),
                lg.generate_log(players[2:4], teams[2:]),
                lg.generate_log((players[1], players[4]), (teams[1], teams[0]))]

        os.makedirs('xgs/tj')
        for i, log in enumerate(logs):
            json.dump(log, open('xgs/tj/battle-{1}-{0}.log.json'
                                .format(i + 1, log['p1rating']['formatid']),
                                'w+'))

        self.p = lp.LogProcessor(StumpMovesetSink(), StumpBattleInfoSink(),
                                 None)

    def check(self, result):
        assert 3 == result

        assert 14 == len(self.p.moveset_sink.sids)
        assert 5 == len(self.p.battle_info_sink.pids)
        assert 4 == len(self.p.battle_info_sink.tids)
        assert {'uu', 'ou'} == set(self.p.battle_info_sink.battles.keys())
        assert 2 == len(self.p.battle_info_sink.battles['uu'])
        assert 1 == len(self.p.battle_info_sink.battles['ou'])

    def test_one_log_at_a_time(self):

        result = 0
        result += self.p.process_logs('xgs/tj/battle-uu-1.log.json',
                                      ref_type='file')
        result += self.p.process_logs('xgs/tj/battle-ou-2.log.json',
                                      ref_type='file')
        result += self.p.process_logs('xgs/tj/battle-uu-3.log.json',
                                      ref_type='file')
        self.check(result)

    def test_with_list_of_files(self):
        result = self.p.process_logs(('xgs/tj/battle-uu-1.log.json',
                                      'xgs/tj/battle-ou-2.log.json',
                                      'xgs/tj/battle-uu-3.log.json'),
                                     ref_type='files')
        self.check(result)

    def test_with_folder(self):
        result = self.p.process_logs('xgs/tj', ref_type='folder')
        self.check(result)

    def test_with_nested_folder(self):
        result = self.p.process_logs('xgs', ref_type='folder')
        self.check(result)

    def test_with_multiple_ref_types(self):
        result = 0
        result += self.p.process_logs('xgs/tj/battle-ou-2.log.json',
                                      ref_type='file')
        result += self.p.process_logs(('xgs/tj/battle-uu-1.log.json',
                                       'xgs/tj/battle-uu-3.log.json'),
                                      ref_type='files')
        self.check(result)

    def teardown_method(self, method):
        shutil.rmtree('xgs', ignore_errors=True)


class TestErrorHandling(object):

    def setup_method(self, method):
        self.p = lp.LogProcessor(StumpMovesetSink(),
                                 StumpBattleInfoSink(),
                                 None)

    def test_unrecognized_metagame(self):
        with pytest.raises(lr.ParsingError) as err:
            self.p.process_logs('battle-asdac-1312.log.json',
                                         ref_type='file')
        assert 'Could not identify a suitable reader' in err.value.args[0]

    def test_nonstandard_metagame(self):
        """Eventually this will actually work"""
        with pytest.raises(lr.ParsingError) as err:
            self.p.process_logs('battle-gen1ou-94543.log.json',
                                         ref_type='file')
        assert 'Could not identify a suitable reader' in err.value.args[0]

    def test_non_json(self):
        with pytest.raises(lr.ParsingError) as err:
            self.p.process_logs('battle-gen1ou-1312.log.afafad',
                                ref_type='file')
        assert 'Could not identify a suitable reader' in err.value.args[0]

    def test_cannot_determine_metagame(self):
        with pytest.raises(lr.ParsingError) as err:
            self.p.process_logs('iyatjfbe.log.json', ref_type='file')
        assert 'Could not identify a suitable reader' in err.value.args[0]

    def test_skip_problematic_log(self):
        assert 0 == self.p.process_logs('iyatjfbe', ref_type='file',
                                        error_handling='skip')

    def test_unknown_ref_type(self):
        with pytest.raises(ValueError) as err:
            self.p.process_logs('battle-uu-845112.log.json', ref_type='thcq')
        assert 'Unrecognized ref_type' in err.value.args[0]

    def test_unknown_error_handling_strategy(self):
        with pytest.raises(ValueError) as err:
            self.p.process_logs('battle-ou-91641.log.json', ref_type='file',
                                error_handling='vyyew')
        assert 'Unrecognized error-handling strategy' in err.value.args[0]

    def test_problem_parsing_log(self):
        """In this case, there is no log..."""
        with pytest.raises(lr.ParsingError) as err:
            self.p.process_logs('battle-nu-134619.log.json', ref_type='file')
        assert 'log not found' in err.value.args[0]


