"""Tests for the log_processor module"""

from onix import utilities
from onix.collection import sinks


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
        self.battles = set()

    def store_battle_info(self, battle_info):
        start_sizes = {'players': len(self.pids),
                       'teams': len(self.tids),
                       'battles': len(self.battles)}

        self.pids.update([player.id for player in battle_info.players])
        self.tids.update([utilities.compute_tid(team)
                          for team in battle_info.slots])
        self.battles.add(battle_info.id)

        return {'players': len(self.pids) - start_sizes['players'],
                'teams': len(self.tids) - start_sizes['teams'],
                'battles': len(self.battles) - start_sizes['battles']}
