"""DAO implementations for SQL backend"""
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
        pass

    def get_total_weight(self, month, metagame, baseline=1630.):
        pass

    def get_usage_by_species(self, month, metagame, species_lookup,
                             baseline=1630.):
        pass
