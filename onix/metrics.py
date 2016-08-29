"""Functionality for calculating ratings, weightings and the like"""

import math


def victory_chance(r1, d1, r2, d2):
    """
    Calculates the expected probability that one player will defeat another,
    based on the players' Glicko ratings.

    See: http://www.glicko.net/research/glicko.pdf

    Args:
        r1 (float) : the first player's Glicko R
        d1 (float) : the first player's Glicko RD
        r2 (float) : the second player's Glicko R
        d2 (float) : the second player's Glicko RD

    Returns:
        float :
            The expected probability that the first player will defeat the
            second

    Examples:
        >>> from onix import metrics
        >>> print(metrics.victory_chance(1695, 43, 1630, 75) #doctest: +ELLIPSIS
        0.5892424...
    """
    c = 3 * math.log(10)**2.0 / (400. * math.pi)**2
    return 1 / (1 + 10**((r2 - r1) / 400. / math.sqrt(1 + c * (d1**2 + d2**2))))


def gxe(r, d, d0=130.0):
    """
    Calculates the GXE (or GLIXARE) rating based on the player's Glicko rating.
    GXE corresponds to the expected win ratio for the player on a ladder with
    no matchmaking. This allows it to be used as a substitute for W/L ratio
    on ladders with matchmaking and also provides a much better ranking metric
    than conventional Glicko-based options such as CREs. For more, see:
    http://www.smogon.com/forums/threads/glixare-a-much-better-way-of-estimating\
    -a-players-overall-rating-than-shoddys-cre.51169/

    Args:
        r (float) : the player's Glicko R
        d (float): the player's Glicko RD
        d0 (float, optional) : the starting RD for the ladder (which should
            correspond to the width of the rating distribution)

    Returns:
        float :
            The player's GXE rating

    Examples:
        >>> from onix import metrics
        >>> print(metrics.gxe(1923, 29)) #doctest: +ELLIPSIS
        0.904029862...
    """
    return victory_chance(r, d, 1500, d0)
