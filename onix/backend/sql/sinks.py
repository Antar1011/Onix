"""Sink implementations for SQL backend"""
import hashlib

import future
import sqlalchemy as sa

from onix import dto
from onix.utilities import compute_sid
from onix.collection import sinks as _sinks
import onix.backend.sql.declarative as dc


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


def _convert_forme(forme):
    return dc.Forme(id=compute_fid(forme),
                    species=forme.species,
                    ability=forme.ability,
                    hp=forme.stats.hp, atk=forme.stats.atk,
                    dfn=forme.stats.dfn, spa=forme.stats.spa,
                    spd=forme.stats.spd, spe=forme.stats.spe)


def _convert_moveset(moveset_dto):
    return dc.Moveset(id=compute_sid(moveset_dto),
                      gender=moveset_dto.gender, item=moveset_dto.item,
                      level=moveset_dto.level, happiness=moveset_dto.happiness,
                      moves=[dc.Move(move=move) for move in moveset_dto.moves],
                      formes=[_convert_forme(forme)
                              for forme in moveset_dto.formes])


class MovesetSink(_sinks.MovesetSink):

    def __init__(self, engine, batch_size=1000):
        self.batch_size = batch_size
        self.buffer = {}
        self.session = sa.orm.sessionmaker(bind=engine)

    def flush(self):
        self.session.bulk_save_objects(self.buffer.values())
        self.session.commit()

    def close(self):
        self.flush()
        self.session.close()

    def store_movesets(self, movesets):
        for sid, moveset in future.iteritems(movesets):
            if sid in self.buffer.keys():
                continue
            self.buffer[sid] = _convert_moveset(moveset)

        if len(self.buffer) >= self.batch_size:
            self.flush()


class BattleInfoSink(_sinks.BattleInfoSink):

    def __init__(self, engine, batch_size=1000):
        self.batch_size = batch_size
        self.buffer = {}
        self.session = sa.orm.sessionmaker(bind=engine)

    def flush(self):
        self.session.bulk_save_objects(self.buffer.values())
        self.session.commit()

    def close(self):
        self.flush()
        self.session.close()

    def store_battle_info(self, battle_info):
        if battle_info.id in self.buffer.keys():
            return






