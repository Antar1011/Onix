"""Data transfer objects"""

import collections

PokeStats_ = collections.namedtuple('PokeStats', ['hp',
                                                  'atk',
                                                  'dfn',
                                                  'spa',
                                                  'spd',
                                                  'spe'])
Moveset_ = collections.namedtuple('Moveset', ['species',
                                              'ability',
                                              'gender',
                                              'item',
                                              'moves',
                                              'stats',
                                              'level',
                                              'happiness'])
Player_ = collections.namedtuple('Player', ['player_id',
                                            'team_id',
                                            'rating'])
BattleInfo_ = collections.namedtuple('BattleInfo', ['id',
                                                    'format',
                                                    'date',
                                                    'p1',
                                                    'p2',
                                                    'turn_length',
                                                    'winner',
                                                    'end_type'])


class PokeStats(PokeStats_):
    """
    Container to represent a Pokemon's stats. This could be base stats, IVs/EVs
    or battle-stats.

    Args:
        hp (int) : hit point stat
        atk (int) : attack stat
        dfn (int) : defense stat (you can't have a field named "def")
        spa (int) : special attack stat
        spd (int) : special defense stat
        spe (int) : speed stat
    """
    pass


class Moveset(Moveset_):
    """
    Container comprising a complete description of a specific build's
    battle-relevant attributes (read: not nickname).

    Args:
        species (str) : species/forme name (appearance-only forms should be
            normalized to the base forme)
        ability (str) : the Pokemon's ability
        gender ('m', 'f' or 'u') : the Pokemon's gender ('u' represents "not
            specified")
        item (str) : the Pokemon's held item
        moves (:obj:`list` of :obj:`str`) : the moves the Pokemon knows
        stats (PokeStats) : the Pokemon's battle stats (that is, not base stats)
        level (int) : the Pokemon's level
        happiness (int) : the Pokemon's happiness

    Note:
        Nature, IVs and EVs aren't included in this description, since there
        might be multiple ways to get to the same battle-stats, but they're all
        functionally equivalent.

    """
    pass


class Player(Player_):
    """
    Container for metadata about a given player/alt

    Args:
        player_id (str) : the player's unique ID
        team_id (str) : hash of the movesets representing the player's team
        rating (dict) : dictionary of player ratings (e.g. Elo, W-L record...).
            The specifics of what's included in this dict will vary based on
            the context.
    """
    pass


class BattleInfo(BattleInfo_):
    """
    Container consisting of metadata for a given battle

    Args:
        id (int) : numerical id of the battle, typically found in the name of
            the log
        format (str) : the metagame of the battle
        date (datetime.date) : the date on which the battle occurred
        p1 (Player) : the first player
        p2 (Player) : the second player
        turn_length (int) : the number of turns in the battle
        winner ("p1", "p2" or ``None``) : the winner of the battle
        end_type (str) : how the battle ended (e.g. "normal" or "forfeit")

    """
    pass
