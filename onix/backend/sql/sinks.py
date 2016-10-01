"""Sink implementations for SQL backend"""
import hashlib

from collections import OrderedDict

from future.utils import iteritems

from onix.model import Moveset, Forme, BattleInfo, Player
from onix.utilities import compute_sid
from onix.collection import sinks as _sinks
from onix.backend.sql import schema


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
        >>> from onix.model import Moveset, Forme, PokeStats
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
        forme (Forme) : the forme to compute the FID for.
        sanitizer (:obj:`onix.utilities.Sanitizer`, optional):
            if no sanitizer is provided, the forme is assumed to be already
            sanitized. Otherwise, the provided ``Sanitizer`` is used to sanitize
            the forme.

    Returns:
        str : the corresponding Forme ID

    Examples:
        >>> from onix.model import Forme, PokeStats
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
    Converts a ``Forme`` object to a row of values in an insert expression into
    the formes table

    Args:
        forme (Forme) : the forme to convert. Is assumed to be
            sanitized.

    Returns:
        tuple : the corresponding row for an insert expression into the formes
            table

    Examples:
        >>> from onix.model import Forme, PokeStats
        >>> from onix.backend.sql.sinks import convert_forme
        >>> forme = Forme('heatmor', 'gluttony',
        ...               PokeStats(333, 241, 170, 253, 150, 204))
        >>> row = convert_forme(forme)
        >>> print(row['ability'])
        gluttony
        >>> print(row['hp'])
        333
    """
    row = dict(id=compute_fid(forme),
               species=forme.species,
               ability=forme.ability)
    row.update(dict(zip(forme.stats._fields, forme.stats)))
    return row


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
        >>> from onix.model import Moveset, Forme, PokeStats
        >>> from onix.backend.sql.sinks import convert_moveset
        >>> from onix.backend.sql import schema
        >>> moveset = Moveset([Forme('diglett', 'sandveil',
        ...                    PokeStats(17, 11, 9, 11, 10, 17))],
        ...                   'm', 'leftovers',
        ...                   ['earthquake', 'rockslide', 'shadowclaw',
        ...                    'substitute'], 5, 255)
        >>> rows = convert_moveset('f4ce673a1', moveset)
        >>> print(rows[schema.movesets][0]['item'])
        leftovers
        >>> print(sum(map(lambda x:len(x), rows.values())))
        7
    """
    rows = dict()

    rows[schema.movesets] = [dict(id=sid,
                                  gender=moveset.gender,
                                  item=moveset.item,
                                  level=moveset.level,
                                  happiness=moveset.happiness)]

    rows[schema.moveslots] = [dict(sid=sid, idx=i, move=move)
                              for i, move in enumerate(moveset.moves)]

    formes = [convert_forme(forme) for forme in moveset.formes]

    rows[schema.formes] = formes

    rows[schema.moveset_forme] = [dict(sid=sid, fid=forme['id'], prime=(i == 0))
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
        >>> print(rows[0]['tid']) #doctest +ELLIPSIS
        8711a93...
        >>> print(rows[1]['sid'])
        def

    """

    team_sids.sort()
    tid = compute_tid(team_sids)
    rows = [dict(tid=tid, idx=i, sid=sid) for i, sid in enumerate(team_sids)]
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
        >>> from onix.model import Player
        >>> from onix.backend.sql.sinks import convert_player
        >>> player = Player(id='chaos', rating={'elo': 1311.1479745117863,
        ...                                     'rpr': None,
        ...                                      'r': 1227.7501280633721,
        ...                                      'l': 83, 'rprd': None,
        ...                                      'rd': 129.53915739500627,
        ...                                      'w': 40})
        >>> row = convert_player(player, 5134, 1, 'aac491ca1')
        >>> print(row['w'])
        40
        >>> print(row['t'])
        None
        >>> print(row['rpr'])
        None
    """
    ratings = {metric: player.rating.get(metric, None)
               for metric in ('w',
                              'l',
                              't',
                              'elo',
                              'r',
                              'rd',
                              'rpr',
                              'rprd')}
    row = dict(bid=bid, side=side, pid=player.id, tid=tid)
    row.update(ratings)
    return row


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
        >>> from onix.model import BattleInfo, Player
        >>> from onix.backend.sql import schema
        >>> from onix.backend.sql.sinks import convert_battle_info
        >>> battle_info = BattleInfo(5776, 'randombattle',
        ...                          datetime.date(2016, 9, 21),
        ...                          [Player('echad', {'w': 1, 'l': 0}),
        ...                           Player('shtaymin', {'w': 0, 'l': 1})],
        ...                          [['abc', 'cab', 'bac'],
        ...                           ['123', '312', '213']], 16, 'forfeit')
        >>> rows = convert_battle_info(battle_info)
        >>> print(rows[schema.battle_players][0]['side'])
        1
        >>> print(rows[schema.battle_players][0]['tid']) #doctest +ELLIPSIS
        267e429f...
        >>> print(rows[schema.teams][0]['tid']) #doctest +ELLIPSIS
        267e429f...
    """
    rows = dict()

    teams = [convert_team(team) for team in battle_info.slots]
    rows[schema.teams] = sum(teams, [])

    rows[schema.battle_infos] = [dict(id=battle_info.id,
                                      format=battle_info.format,
                                      date=battle_info.date,
                                      turns=battle_info.turn_length,
                                      end_type=battle_info.end_type)]

    rows[schema.battle_players] = [convert_player(player, battle_info.id,
                                                  i + 1, teams[i][0]['tid'])
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
        with connection.begin() as transaction:
            for table, rows in iteritems(self.cache):
                connection.execute(table.insert(), rows)
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
        self.insert_handler = _InsertHandler(schema.movesets,
                                             schema.moveslots,
                                             schema.formes,
                                             schema.moveset_forme)

    def flush(self):
        self.insert_handler.perform_inserts(self.conn)
        self.count = 0

    def close(self):
        self.flush()

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
        self.insert_handler = _InsertHandler(schema.teams,
                                             schema.battle_infos,
                                             schema.battle_players)

    def flush(self):
        self.insert_handler.perform_inserts(self.conn)
        self.count = 0

    def close(self):
        self.flush()

    def store_battle_info(self, battle_info):
        self.insert_handler.add_to_cache(convert_battle_info(battle_info))
        self.count += 1

        if self.count >= self.batch_size:
            self.flush()
