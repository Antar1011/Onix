"""Tests for the log_processor module"""
import datetime
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

    log = lg.generate_log(players, [[moveset, moveset]])

    try:
        json.dump(log, open('battle-randombattle-134341313.log.json', 'w+'))
        p = lp.LogProcessor(None, None, None)
        result = p.process_logs('battle-randombattle-134341313.log.json',
                                ref_type='file',
                                format='randombattle',
                                date=datetime.datetime(2016, 8, 31))
        assert 1 == result

    finally:
        os.remove('egagadga.log.json')


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
        json.dump(log, open('wtafda.log.json', 'w+'))
        p = lp.LogProcessor(StumpMovesetSink(), StumpBattleInfoSink(), None)
        p.process_logs('wtafda.log.json', ref_type='file',
                       format='ou', date=datetime.datetime(2016, 8, 31))

        result = p.process_logs('egagadga.log.json', ref_type='file',
                                format='ou',
                                date=datetime.datetime(2016, 8, 31))
        assert 1 == result

        assert 11 == len(p.moveset_sink.sids)
        assert 2 == len(p.battle_info_sink.pids)
        assert 2 == len(p.battle_info_sink.tids)
        assert {'ou'} == set(p.battle_info_sink.battles.keys())
        assert 1 == len(p.battle_info_sink.battles['ou'])

    finally:
        os.remove('wtafda.log.json')





