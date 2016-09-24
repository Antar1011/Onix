"""DAO implementations for SQL backend"""
import calendar
import datetime

import sqlalchemy as sa

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

    def get_number_of_battles(self, month, metagame):
        month_start = datetime.datetime.strptime(month, '%Y%m').date()
        _, last_day_of_month = calendar.monthrange(month_start.year,
                                                   month_start.month)
        month_end = datetime.date(month_start.year, month_start.month,
                                  last_day_of_month)
        battle_infos = model.BattleInfo.__table__
        query = (sa.select([sa.func.count()])
                 .where(battle_infos.c.format == metagame)
                 .where(battle_infos.c.date.between(month_start, month_end))
                 .where(battle_infos.c.turns >= 6)
                 .select_from(battle_infos))
        result = self.conn.execute(query)
        return result.fetchone()[0]

    def get_total_weight(self, month, metagame, baseline=1630.):
        pass

    def get_usage_by_species(self, month, metagame, species_lookup,
                             baseline=1630.):
        pass
