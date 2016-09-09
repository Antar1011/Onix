"""Sink implementations for SQL backend"""
import hashlib

from onix import dto
from onix import utilities
from onix.backend.sql import declarative


def compute_fid(forme):
    """
    Computes the Forme ID for a given forme

    Args:
        forme (dto.Forme) : the forme to compute the FID for. Is assumed to be
            sanitized.

    Returns:
        str : the corresponding Forme ID

    Examples:
        >>> from onix.dto import Forme, PokeStats
        >>> from onix.backend.sql.sinks import compute_fid
        >>> forme = Forme('stunfisk', 'static',
        ...               PokeStats(369, 168, 177, 258, 225, 73))
        >>> print(compute_fid(forme)) #doctest: +ELLIPSIS
        tbd
    """
    forme_hash = hashlib.sha512(repr(forme).encode('utf-8')).hexdigest()

    # may eventually want to truncate hash, e.g.
    # forme_hash = forme_hash[:16]

    return forme_hash
