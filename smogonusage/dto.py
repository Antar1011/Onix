"""Data transfer objects"""

import collections

PokeStats = collections.namedtuple('PokeStats', ['hp',
                                                 'atk',
                                                 'dfn',
                                                 'spa',
                                                 'spd',
                                                 'spe'])

Moveset = collections.namedtuple('Moveset', ['species',
                                             'ability',
                                             'gender',
                                             'item',
                                             'moves',
                                             'stats',
                                             'level',
                                             'happiness'])

Player = collections.namedtuple('Player', ['player_id',
                                           'team_id',
                                           'rating'])

BattleInfo = collections.namedtuple('BattleInfo', ['id',
                                                   'format',
                                                   'date',
                                                   'p1',
                                                   'p2',
                                                   'turn_length',
                                                   'winner',
                                                   'end_type'])

Matchup = collections.namedtuple('Matchup', ['battle_id',
                                             'p1_sid',
                                             'p2_sid',
                                             'turn_start',
                                             'turn_end',
                                             'outcome'])
