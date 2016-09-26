"""Sink implementations for SQL backend"""
import hashlib

from collections import OrderedDict

from future.utils import iteritems

from onix import dto
from onix.dto import Moveset
from onix.utilities import compute_sid
from onix.collection import sinks as _sinks
from onix.backend.sql import model


def compute_tid(team, sanitizer=None):
    """
    Computes the Team ID for the given group of movesets

    Args:
        team (:obj:`iterable` of :obj:`Moveset` or :obj:`str`) :
            the team for which to compute the TID, represented either by their
            movesets or by their SIDs
        sanitizer (:obj:`onix.utilities.Sanitizer`, optional):
            if no sanitizer is provided, movesets are assumed to be already
            sanitized. Otherwise, the provided ``Sanitizer`` is used to sanitize
            the movesets.

    Returns:
        str: the corresponding Team ID

    Examples:
        >>> from onix.dto import Moveset, Forme, PokeStats
        >>> from onix.backend.sql.sinks import compute_tid
        >>> delphox = Moveset([Forme('delphox', 'magician',
        ...                    PokeStats(282, 158, 222, 257, 220, 265))],
        ...                   'f', 'lifeorb', ['calmmind', 'psychic'], 100, 255)
        >>> ditto = Moveset([Forme('ditto', 'imposter',
        ...                  PokeStats(259, 164, 98, 134, 126, 123))],
        ...                  'u', 'focussash', ['transform'], 100, 255)
        >>> print(compute_tid([delphox, ditto])) #doctest: +ELLIPSIS
        4e49b0eb...
    """
    if isinstance(team[0], Moveset):
        sids = [compute_sid(moveset, sanitizer) for moveset in team]
    elif isinstance(team[0], str):
        sids = team
    else:
        raise TypeError('team is neither an iterable of movesets nor SIDs')
    sids = sorted(sids)
    team_hash = hashlib.sha512(repr(sids).encode('utf-8')).hexdigest()

    # may eventually want to truncate hash, e.g.
    # team_hash = team_hash[:16]

    return team_hash


def compute_fid(forme, sanitizer=None):
    """
    Computes the Forme ID for a given forme

    Args:
        forme (dto.Forme) : the forme to compute the FID for.
        sanitizer (:obj:`onix.utilities.Sanitizer`, optional):
            if no sanitizer is provided, the forme is assumed to be already
            sanitized. Otherwise, the provided ``Sanitizer`` is used to sanitize
            the forme.

    Returns:
        str : the corresponding Forme ID

    Examples:
        >>> from onix.dto import Forme, PokeStats
        >>> from onix.backend.sql.sinks import compute_fid
        >>> forme = Forme('stunfisk', 'static',
        ...               PokeStats(369, 168, 177, 258, 225, 73))
        >>> print(compute_fid(forme)) #doctest: +ELLIPSIS
        2220c1624d...
    """
    if sanitizer is not None:
        forme = sanitizer.sanitize(forme)
    forme_hash = hashlib.sha512(repr(forme).encode('utf-8')).hexdigest()

    # may eventually want to truncate hash, e.g.
    # forme_hash = forme_hash[:16]

    return forme_hash


def convert_forme(forme):
    """
    Converts a Forme DTO to a row of values in an insert expression into the
    formes table

    Args:
        forme (dto.Forme) : the forme to convert. Is assumed to be
            sanitized.

    Returns:
        tuple : the corresponding row for an insert expression into the formes
            table

    Examples:
        >>> from onix.dto import Forme, PokeStats
        >>> from onix.backend.sql.sinks import convert_forme
        >>> forme = Forme('heatmor', 'gluttony',
        ...               PokeStats(333, 241, 170, 253, 150, 204))
        >>> row = convert_forme(forme)
        >>> print(row) #doctest: +ELLIPSIS
        ('379bf3...', 'heatmor', 'gluttony', 333, 241, 170, 253, 150, 204)
    """
    return (compute_fid(forme), forme.species, forme.ability) + forme.stats


def convert_moveset(sid, moveset):
    """
    Converts a Moveset DTO to rows of values for insert expressions

    Args:
        sid (str) : the SID of the moveset
        moveset (dto.Moveset) : the moveset to convert. Is assumed to be
            sanitized.

    Returns:
        :obj:`dict` of :obj:`sa.Table` to :obj:`list` of :obj:`tuple` :
            the corresponding insert rows. The keys are the table names, the
            values are the rows to insert.

    Examples:
        >>> from onix.dto import Moveset, Forme, PokeStats
        >>> from onix.backend.sql.sinks import convert_moveset
        >>> from onix.backend.sql import model
        >>> moveset = Moveset([Forme('diglett', 'sandveil',
        ...                    PokeStats(17, 11, 9, 11, 10, 17))],
        ...                   'm', 'leftovers',
        ...                   ['earthquake', 'rockslide', 'shadowclaw',
        ...                    'substitute'], 5, 255)
        >>> rows = convert_moveset('f4ce673a1', moveset)
        >>> print(rows[model.movesets]) #doctest: +ELLIPSIS
        [('f4ce673...', 'm', 'leftovers', 5, 255)]
        >>> print(sum(map(lambda x:len(x), rows.values())))
        7
    """
    rows = dict()

    rows[model.movesets] = [(sid,
                             moveset.gender,
                             moveset.item,
                             moveset.level,
                             moveset.happiness)]

    rows[model.moveslots] = [(sid, i, move)
                             for i, move in enumerate(moveset.moves)]

    formes = [convert_forme(forme) for forme in moveset.formes]

    rows[model.formes] = formes

    rows[model.moveset_forme] = [(sid, forme[0], i == 0)
                                 for i, forme in enumerate(formes)]

    return rows


def convert_team(team_sids):
    """
    Converts a list of SIDs specifying a player's team into the corresponding
    rows of values for an insert expression into the teams table

    Args:
        team_sids (:obj:`list` of :obj:`str`) : the SIDs corresponding to a
            player's pokemon

    Returns:
        :obj:`list` of :obj:`tuple` :
            The corresponding rows for an insert expression into the teams table

    Examples:
        >>> from onix.backend.sql.sinks import convert_team
        >>> rows = convert_team(['ghi', 'abc', 'def'])
        >>> print(rows[0][0]) #doctest +ELLIPSIS
        8711a93...
        >>> print(rows[1][2])
        def

    """

    team_sids.sort()
    tid = compute_tid(team_sids)
    rows = [(tid, i, sid) for i, sid in enumerate(team_sids)]
    return rows


def convert_player(player, bid, side, tid):
    """
    Converts a Players DTO to a row of values in an insert expression into the
    battle_players table

    Args:
        player (dto.Player) : the Player to convert

        bid (int) : the battle ID

        side (int) : the player's "index" in the battle.

            .. note::
                this index is one-based rahter than zero-based, so as to
                maintain consistency with log references (*i.e.* "player 1 vs.
                player 2").

        tid (str) : the TID for the player's team

    Returns:
        tuple : the corresponding row for an insert expression into the
            battle_players table

    Examples:
        >>> from onix.dto import Player
        >>> from onix.backend.sql.sinks import convert_player
        >>> player = Player(id='chaos', rating={'elo': 1311.1479745117863,
        ...                                     'rpr': None,
        ...                                      'r': 1227.7501280633721,
        ...                                      'l': 83, 'rprd': None,
        ...                                      'rd': 129.53915739500627,
        ...                                      'w': 40})
        >>> row = convert_player(player, 5134, 1, 'aac491ca1')
        >>> print(row[4])
        40
        >>> print(row[6])
        None
        >>> print(row[10])
        None
    """
    ratings = tuple(player.rating.get(metric, None)
                    for metric in ('w',
                                   'l',
                                   't',
                                   'elo',
                                   'r',
                                   'rd',
                                   'rpr',
                                   'rprd'))
    return (bid, side, player.id, tid) + ratings


def convert_battle_info(battle_info):
    """
    Converts a Moveset DTO to rows of values for insert expressions

    Args:
        battle_info (dto.BattleInfo) : the BattleInfo to convert

    Returns:
        :obj:`dict` of :obj:`sa.Table` to :obj:`list` of :obj:`tuple` :
            the corresponding insert rows. The keys are the table names, the
            values are the rows to insert.

    Examples:
        >>> import datetime
        >>> from onix.dto import BattleInfo, Player
        >>> from onix.backend.sql import model
        >>> from onix.backend.sql.sinks import convert_battle_info
        >>> battle_info = BattleInfo(5776, 'randombattle',
        ...                          datetime.date(2016, 9, 21),
        ...                          [Player('echad', {'w': 1, 'l': 0}),
        ...                           Player('shtaymin', {'w': 0, 'l': 1})],
        ...                          [['abc', 'cab', 'bac'],
        ...                           ['123', '312', '213']], 16, 'forfeit')
        >>> rows = convert_battle_info(battle_info)
        >>> print(rows[model.battle_players][0][1])
        1
        >>> print(rows[model.battle_players][0][3]) #doctest +ELLIPSIS
        267e429f...
        >>> print(rows[model.teams][0][0])
        267e429f...
    """
    rows = dict()

    teams = [convert_team(team) for team in battle_info.slots]
    rows[model.teams] = sum(teams, [])

    rows[model.battle_infos] = [(battle_info.id,
                                 battle_info.format,
                                 battle_info.date,
                                 battle_info.turn_length,
                                 battle_info.end_type)]

    rows[model.battle_players] = [convert_player(player, battle_info.id,
                                                 i + 1, teams[i][0][0])
                                  for i, player
                                  in enumerate(battle_info.players)]

    return rows


class _InsertHandler(object):
    """
    Handler for caching SQL inserts and executing them in bulk

    Args:
        *tables (:obj:`list` of :obj:`sa.Table`) : the tables to perform inserts
            into, in the order in which inserts should be performed
    """

    def __init__(self, *tables):
        self.tables = tables
        self.cache = self._new_cache()

    def _new_cache(self):
        """
        Creates an empty cache

        Returns:
            dict : the empty cache
        """
        cache = OrderedDict()
        for table in self.tables:
            cache[table] = []
        return cache

    def add_to_cache(self, inserts):
        """
        Add insert rows to the cache

        Args:
            inserts (`dict`) : the rows to insert, with the keys being the
                tables into which the rows will be inserted

        Returns:
            None
        """
        for table, rows in iteritems(inserts):
            self.cache[table] += rows

    def perform_inserts(self, connection):
        for table, rows in iteritems(self.cache):
            connection.execute(table.insert().values(rows))
        self.cache = self._new_cache()


class MovesetSink(_sinks.MovesetSink):
    """
    SQL implementation of the MovesetSink interface

    Args:
        connection (sqlalchemy.engine.base.Connection) :
            connection to the SQL backend
        batch_size (:obj:`int`, optional) :
            the number of movesets to go through before actually committing
            to the database, defaults to 1000
    """
    def __init__(self, connection, batch_size=1000):
        self.count = 0
        self.batch_size = batch_size
        self.conn = connection
        self.insert_handler = _InsertHandler(model.movesets,
                                             model.moveslots,
                                             model.formes,
                                             model.moveset_forme)

    def flush(self):
        self.insert_handler.perform_inserts(self.conn)
        self.count = 0

    def close(self):
        self.flush()
        self.conn.close()

    def store_movesets(self, movesets):
        for sid, moveset in iteritems(movesets):
            self.insert_handler.add_to_cache(convert_moveset(sid, moveset))
            self.count += 1

        if self.count >= self.batch_size:
            self.flush()


class BattleInfoSink(_sinks.BattleInfoSink):
    """
    SQL implementation of the MovesetSink interface

    Args:
        connection (sqlalchemy.engine.base.Connection) :
            connection to the SQL backend
        batch_size (:obj:`int`, optional) :
            the number of battles to go through before actually committing
                to the database, defaults to 100
    """
    def __init__(self, connection, batch_size=100):
        self.count = 0
        self.batch_size = batch_size
        self.conn = connection
        self.insert_handler = _InsertHandler(model.teams,
                                             model.battle_infos,
                                             model.battle_players)

    def flush(self):
        self.insert_handler.perform_inserts(self.conn)
        self.count = 0

    def close(self):
        self.flush()
        self.conn.close()

    def store_battle_info(self, battle_info):
        self.insert_handler.add_to_cache(convert_battle_info(battle_info))
        self.count += 1

        if self.count >= self.batch_size:
            self.flush()
