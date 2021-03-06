"""Onix's fundamental data types"""

from collections import namedtuple


class PokeStats(namedtuple('PokeStats', ['hp',
                                         'atk',
                                         'dfn',
                                         'spa',
                                         'spd',
                                         'spe'])):
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


class Forme(namedtuple('Forme', ['species',
                                 'ability',
                                 'stats'])):
    """
    Container to represent a Pokemon's Forme (that is, the aspects of a moveset
    that might change when forme changes).

    Args:
        species (str) : forme name
        ability (str) : the Pokemon's ability
        stats (PokeStats) : the Pokemon's battle stats (that is, not base stats)
    """


class Moveset(namedtuple('Moveset', ['formes',
                                     'gender',
                                     'item',
                                     'moves',
                                     'level',
                                     'happiness'])):
    """
    Container comprising a complete description of a specific build's
    battle-relevant attributes (read: not nickname).

    Args:
        formes (:obj:`list` of :obj:`Forme`) : the formes the Pokemon might
            take over the course of the battle

            .. note ::
                The first forme in this list is considered the Pokemon's
                "primary forme." It is the forme the Pokemon will appear in
                the first time it appears on the field (making an exception for
                orb-holding Groudon and Kyogre who transform immediately into
                their Primal formes and do not change back)

        gender ('m', 'f' or 'u') : the Pokemon's gender ('u' represents "not
            specified")
        item (str) : the Pokemon's held item
        moves (:obj:`list` of :obj:`str`) : the moves the Pokemon knows
        level (int) : the Pokemon's level
        happiness (int) : the Pokemon's happiness

    Note:
        Nature, IVs and EVs aren't included in this description, since there
        might be multiple ways to get to the same battle-stats, but they're all
        functionally equivalent.

    """
    pass


class Player(namedtuple('Player', ['id',
                                   'rating'])):
    """
    Container for metadata about a given player/alt

    Args:
        id (str) : the player's unique ID
        rating (dict) : dictionary of player ratings (e.g. Elo, W-L record...).
            The specifics of what's included in this dict will vary based on
            the context.
    """
    pass


class BattleInfo(namedtuple('BattleInfo', ['id',
                                           'format',
                                           'date',
                                           'players',
                                           'slots',
                                           'turn_length',
                                           'end_type'])):
    """
    Container consisting of metadata for a given battle

    Args:
        id (int) : numerical id of the battle, typically found in the name of
            the log
        format (str) : the metagame of the battle
        date (datetime.date) : the date on which the battle occurred
        players (:obj:`list` of :obj:`Player`) : the battle participants
        slots (:obj:`list` of `list` of str) : the set IDs for the Pokemon
            on each player's team. Should have the same length as ``players``
        turn_length (int) : the number of turns in the battle
        end_type (str) : how the battle ended (e.g. "normal" or "forfeit")

    """
    pass
