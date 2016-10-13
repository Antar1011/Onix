"""Tests for the log_processor module"""
import json
import warnings

import pytest

from collections import defaultdict

from onix.backend.sql.sinks import compute_tid
from onix import contexts
from onix.collection import log_reader as lr
from onix.collection import log_processor as lp
from onix.collection import sinks
from onix.scripts import log_generator as lg


class StumpMovesetSink(sinks.MovesetSink):
    """MovesetSink implementation that just adds the SIDs to a set"""

    def __init__(self):
        self.sids = set()

    def store_movesets(self, movesets):
        self.sids.update(movesets.keys())

    def flush(self):
        pass

    def close(self):
        self.flush()


class StumpBattleInfoSink(sinks.BattleInfoSink):
    """BattleInfoSink that just keeps track of sets of unique IDs"""

    def __init__(self):
        self.pids = set()
        self.tids = set()
        self.battles = defaultdict(set)

    def store_battle_info(self, battle_info):

        self.pids.update([player.id for player in battle_info.players])
        self.tids.update([compute_tid(team) for team in battle_info.slots])
        self.battles[battle_info.format].add(battle_info.id)

    def flush(self):
        pass

    def close(self):
        self.flush()


@pytest.fixture()
def moveset_sink():
    with StumpMovesetSink() as moveset_sink:
        yield moveset_sink


@pytest.fixture()
def battle_info_sink():
    with StumpBattleInfoSink() as battle_info_sink:
        yield battle_info_sink


@pytest.fixture()
def p(moveset_sink, battle_info_sink):
    return lp.LogProcessor(moveset_sink, battle_info_sink, None)


def test_processor_without_sinks(tmpdir):
    """Should still work, should still parse the logs, even though nothing
    actually gets persisted"""
    context = contexts.get_standard_context()

    players = [lg.generate_player(username)[0]
               for username in ['Alice', 'Bob']]

    moveset, _ = lg.generate_pokemon('articuno', context)

    log = lg.generate_log(players, [[moveset], [moveset]])

    log_ref = '{0}/battle-randombattle-134341313.log.json'.format(
        tmpdir.strpath)
    json.dump(log, open(log_ref, 'w+'))
    p = lp.LogProcessor(None, None, None)
    result = p.process_logs(log_ref, ref_type='file')
    assert 1 == result


def test_process_single_log(moveset_sink, battle_info_sink, p, tmpdir):
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

    log_ref = '{0}/battle-ou-195629539.log.json'.format(tmpdir.strpath)


    json.dump(log, open(log_ref, 'w+'))

    result = p.process_logs(log_ref, ref_type='file')

    assert 1 == result

    assert 11 == len(moveset_sink.sids)
    assert 2 == len(battle_info_sink.pids)
    assert 2 == len(battle_info_sink.tids)
    assert {'ou'} == set(battle_info_sink.battles.keys())
    assert 1 == len(battle_info_sink.battles['ou'])


class TestProcessMultipleLogs(object):

    @staticmethod
    @pytest.fixture()
    def generate_logs(tmpdir):
        context = contexts.get_standard_context()

        players = [lg.generate_player(username, formatid='uu')[0]
                   for username in ('Alice', 'Bob')]
        players += [lg.generate_player(username, formatid='ou')[0]
                    for username in ('Charley', 'Delia')]
        players.append(lg.generate_player('Eve', formatid='uu')[0])

        movesets = [lg.generate_pokemon(species, context)[0]
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

        tmpdir.mkdir('tj')
        for i, log in enumerate(logs):
            json.dump(log, open('{2}/tj/battle-{1}-{0}.log.json'
                                .format(i + 1, log['p1rating']['formatid'],
                                        tmpdir.strpath),
                                'w+'))

    def check(self, processor, result):
        assert 3 == result

        assert 14 == len(processor.moveset_sink.sids)
        assert 5 == len(processor.battle_info_sink.pids)
        assert 4 == len(processor.battle_info_sink.tids)
        assert {'uu', 'ou'} == set(processor.battle_info_sink.battles.keys())
        assert 2 == len(processor.battle_info_sink.battles['uu'])
        assert 1 == len(processor.battle_info_sink.battles['ou'])

    @pytest.mark.usefixtures("generate_logs")
    def test_one_log_at_a_time(self, tmpdir, p):

        result = 0
        result += p.process_logs('{0}/tj/battle-uu-1.log.json'.format(
            tmpdir.strpath), ref_type='file')
        result += p.process_logs('{0}/tj/battle-ou-2.log.json'.format(
            tmpdir.strpath), ref_type='file')
        result += p.process_logs('{0}/tj/battle-uu-3.log.json'.format(
            tmpdir.strpath), ref_type='file')
        self.check(p, result)

    @pytest.mark.usefixtures("generate_logs")
    def test_with_list_of_files(self, tmpdir, p):
        result = p.process_logs(('{0}/tj/battle-uu-1.log.json'.format(
            tmpdir.strpath),
                                 '{0}/tj/battle-ou-2.log.json'.format(
            tmpdir.strpath),
                                 '{0}/tj/battle-uu-3.log.json'.format(
            tmpdir.strpath)), ref_type='files')
        self.check(p, result)

    @pytest.mark.usefixtures("generate_logs")
    def test_with_folder(self, tmpdir, p):
        result = p.process_logs('{0}/tj'.format(tmpdir.strpath),
                                ref_type='folder')
        self.check(p, result)

    @pytest.mark.usefixtures("generate_logs")
    def test_with_nested_folder(self, tmpdir, p):
        result = p.process_logs(tmpdir.strpath, ref_type='folder')
        self.check(p, result)

    @pytest.mark.usefixtures("generate_logs")
    def test_with_multiple_ref_types(self, tmpdir, p):
        result = 0
        result += p.process_logs('{0}/tj/battle-ou-2.log.json'.format(
            tmpdir.strpath), ref_type='file')
        result += p.process_logs(('{0}/tj/battle-uu-1.log.json'.format(
            tmpdir.strpath), '{0}/tj/battle-uu-3.log.json'.format(
            tmpdir.strpath)), ref_type='files')
        self.check(p, result)


class TestErrorHandling(object):

    def test_unrecognized_metagame(self, p):
        with pytest.raises(lr.ParsingError) as err:
            p.process_logs('battle-asdac-1312.log.json',
                                         ref_type='file')
        assert 'Could not identify a suitable reader' in err.value.args[0]

    def test_nonstandard_metagame(self, p):
        """Eventually this will actually work"""
        with pytest.raises(lr.ParsingError) as err:
            p.process_logs('battle-gen1ou-94543.log.json',
                                         ref_type='file')
        assert 'Could not identify a suitable reader' in err.value.args[0]

    def test_non_json(self, p):
        with pytest.raises(lr.ParsingError) as err:
            p.process_logs('battle-gen1ou-1312.log.afafad',
                                ref_type='file')
        assert 'Could not identify a suitable reader' in err.value.args[0]

    def test_cannot_determine_metagame(self, p):
        with pytest.raises(lr.ParsingError) as err:
            p.process_logs('iyatjfbe.log.json', ref_type='file')
        assert 'Could not identify a suitable reader' in err.value.args[0]

    def test_skip_problematic_log(self, p):
        assert 0 == p.process_logs('iyatjfbe', ref_type='file',
                                        error_handling='skip')

    def test_unknown_ref_type(self, p):
        with pytest.raises(ValueError) as err:
            p.process_logs('battle-uu-845112.log.json', ref_type='thcq')
        assert 'Unrecognized ref_type' in err.value.args[0]

    def test_unknown_error_handling_strategy(self, p):
        with pytest.raises(ValueError) as err:
            p.process_logs('battle-ou-91641.log.json', ref_type='file',
                                error_handling='vyyew')
        assert 'Unrecognized error-handling strategy' in err.value.args[0]

    def test_problem_parsing_log(self, p):
        """In this case, there is no log..."""
        with pytest.raises(lr.ParsingError) as err:
            p.process_logs('battle-nu-134619.log.json', ref_type='file')
        assert 'log not found' in err.value.args[0]


