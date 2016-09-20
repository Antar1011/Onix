"""Sink implementations for SQL backend"""
import hashlib

import future
import sqlalchemy as sa

from onix import dto
from onix.utilities import compute_sid, compute_tid
from onix.collection import sinks as _sinks
from onix.backend.sql import model


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


def _convert_forme(forme_dto):
    """
    Converts a Forme DTO to the corresponding ORM object

    Args:
        forme_dto (dto.Forme) : the forme to convert. Is assumed to be
            sanitized.

    Returns:
        model.Forme : the corresponding ORM object

    Examples:

    """
    # TODO: Examples
    return model.Forme(id=compute_fid(forme_dto),
                       species=forme_dto.species,
                       ability=forme_dto.ability,
                       hp=forme_dto.stats.hp, atk=forme_dto.stats.atk,
                       dfn=forme_dto.stats.dfn, spa=forme_dto.stats.spa,
                       spd=forme_dto.stats.spd, spe=forme_dto.stats.spe)


def _convert_moveset(moveset_dto):
    """
    Converts a Moveset DTO to the corresponding ORM object

    Args:
        moveset_dto (dto.Moveset) : the moveset to convert. Is assumed to be
            sanitized.

    Returns:
        model.Moveset : the corresponding ORM object, including any child
            classes

    Examples:

    """
    # TODO: Examples
    return model.Moveset(id=compute_sid(moveset_dto),
                         gender=moveset_dto.gender, item=moveset_dto.item,
                         level=moveset_dto.level,
                         happiness=moveset_dto.happiness,
                         moves=[model._Move(move=move)
                                for move in moveset_dto.moves],
                         formes=[_convert_forme(forme)
                                 for forme in moveset_dto.formes])


def _convert_battle_info(battle_info_dto):
    """
    Converts a BattleInfo DTO to the corresponding ORM object

    Args:
        battle_info_dto (dto.BattleInfo) : the BattleInfo to convert

    Returns:
        model.BattleInfo : the corresponding ORM object, including any child
            classes

    Examples:

    """
    # TODO: Examples


class MovesetSink(_sinks.MovesetSink):

    def __init__(self, engine, batch_size=1000):
        self.batch_size = batch_size
        self.buffer = {}
        self.session = sa.orm.sessionmaker(bind=engine)

    def flush(self):
        self.session.bulk_save_objects(self.buffer.values())
        self.session.commit()
        self.buffer = {}

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
        if battle_info.id in self.battle_info_buffer.keys():
            return
        for team in battle_info.slots:
            team

        self.buffer[battle_info.id] = _convert_battle_info(battle_info)

        if len(self.battle_info_buffer) >= self.batch_size:
            self.flush()






