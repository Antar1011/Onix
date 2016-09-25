"""DAO implementations for SQL backend"""
import calendar
import datetime

import sqlalchemy as sa

from onix import metrics
from onix.reporting import dao as _dao
from onix.backend.sql import model


class ReportingDAO(_dao.ReportingDAO):
    """
    SQL implementation of ReportingDAO interface

    Args:
        connection (sqlalchemy.engine.base.Connection) :
            connection to the SQL backend
    """
    def __init__(self, connection):
        self.conn = connection
        self.conn.connection.create_function('weight', 3, metrics.skill_chance)

    def _filter_battles(self, month, metagame):
        battle_infos = model.BattleInfo.__table__

        month_start = datetime.datetime.strptime(month, '%Y%m').date()
        _, last_day_of_month = calendar.monthrange(month_start.year,
                                                   month_start.month)
        month_end = datetime.date(month_start.year, month_start.month,
                                  last_day_of_month)

        query = (sa.select([battle_infos.c.id])
                 .select_from(battle_infos)
                 .where(battle_infos.c.format == metagame)
                 .where(battle_infos.c.date.between(month_start, month_end)))

        # filter out early forfeits -- TODO: logic to handle non-6v6
        query = query.where(battle_infos.c.turns >= 6)
        return query.alias()

    def _weight_players(self, baseline):
        battle_players = model.BattlePlayer.__table__

        # policy is to use provisional ratings
        r = battle_players.c.rpr
        rd = battle_players.c.rprd

        if baseline == 0.:
            weight = sa.literal_column("1")
        elif baseline > 1500.:
            weight = sa.case([(rd > 100., 0)],
                             else_=sa.func.weight(r, rd, baseline))
        else:
            weight = sa.func.weight(r, rd, baseline)
        query = sa.select([battle_players.c.bid,
                           battle_players.c.tid,
                           weight.label('weight')]).select_from(battle_players)
        return query.alias()

    def get_number_of_battles(self, month, metagame):
        query = self._filter_battles(month, metagame)
        query = sa.select([sa.func.count()]).select_from(query)

        result = self.conn.execute(query)
        return result.fetchone()[0]

    def get_total_weight(self, month, metagame, baseline=1630.):
        battles = self._filter_battles(month, metagame)
        players = self._weight_players(baseline)

        join = sa.join(battles, players, onclause=battles.c.id == players.c.bid)
        query = sa.select([sa.func.sum(players.c.weight)]).select_from(join)

        result = self.conn.execute(query)
        return result.fetchone()[0] or 0

    def get_usage_by_species(self, month, metagame, species_lookup,
                             baseline=1630.):
        pass
