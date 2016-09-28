"""DAO implementations for SQL backend"""
import calendar
import datetime

import sqlalchemy as sa

from onix import metrics
from onix.reporting import dao as _dao
from onix.backend.sql import schema


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

    def _filtered_battles(self, month, metagame):
        """
        Filter out battles that are not in the date range, not the right
        metagame or are too short (early forfeit policy)

        Args:
           month (str) :
                the month to analyze
            metagame (str) :
                the sanitized name of the metagame

        Returns:
            sa.sql.expression.Alias :
                the filtered view of the battle_infos table
        """
        battle_infos = schema.battle_infos

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

    def get_number_of_battles(self, month, metagame):
        query = self._filtered_battles(month, metagame)
        query = sa.select([sa.func.count()]).select_from(query)

        result = self.conn.execute(query)
        return result.fetchone()[0]

    def _weighted_players(self, battles, baseline):
        """
        Gets player weights for the specified battles

        Args:
            battles (sa.sql.expression.Alias) :
                the relevant battles
            baseline (float) :
                the baseline to use for  skill_chance. Defaults to 1630.

                .. note ::
                   a baseline of zero corresponds to unweighted stats

        Returns:
            sa.sql.expression.Alias :
                the relevant battle_players table with weight added
        """
        players = schema.battle_players

        join = sa.join(battles, players, onclause=battles.c.id == players.c.bid)
        query = sa.select([battles.c.id.label('bid'),
                           players.c.side.label('side'),
                           players.c.pid.label('pid'),
                           players.c.tid.label('tid'),
                           players.c.w.label('w'),
                           players.c.l.label('l'),
                           players.c.t.label('t'),
                           players.c.elo.label('elo'),
                           players.c.r.label('r'),
                           players.c.rd.label('rd'),
                           players.c.rpr.label('rpr'),
                           players.c.rprd.label('rprd')]).select_from(join)
        filtered = query.alias()

        # policy is to use provisional ratings
        r = sa.func.ifnull(filtered.c.rpr, 1500.)
        rd = sa.func.ifnull(filtered.c.rprd, 130.)

        if baseline == 0.:
            weight = sa.literal_column("1")
        elif baseline > 1500.:
            weight = sa.case([(rd > 100., 0)],
                             else_=sa.func.weight(r, rd, baseline))
        else:
            weight = sa.func.weight(r, rd, baseline)
        query = sa.select([filtered.c.bid,
                           filtered.c.side,
                           filtered.c.pid,
                           filtered.c.tid,
                           weight.label('weight')]).select_from(filtered)
        return query.alias()

    def get_total_weight(self, month, metagame, baseline=1630.):
        players = self._weighted_players(
            self._filtered_battles(month, metagame), baseline)

        query = sa.select([sa.func.sum(players.c.weight)]).select_from(players)

        result = self.conn.execute(query)
        return result.fetchone()[0] or 0

    def _weighted_team_members(self, players, species_lookup):
        """
        Gets weights for individual team members and prettifies species names

        Args:
            players (sa.sql.expression.Alias) :
                The relevant players with weights
            species_lookup (dict) :
                mapping of species names or forme-concatenations to their
                display names. This is what handles things like determining
                whether megas re tiered together or separately or what counts as
                an "appearance-only" forme.

        Returns:
            sa.sql.expression.Alias :
                the relevant teams table with prettified species names and
                weights added

        """
        teams = schema.teams
        mf = schema.moveset_forme
        formes = schema.formes

        join = sa.join(players, teams, onclause=players.c.tid == teams.c.tid)
        join = join.join(mf, onclause=teams.c.sid == mf.c.sid)
        join = join.join(formes, onclause=mf.c.fid == formes.c.id)

        join = (sa.select([players.c.bid.label('bid'),
                           players.c.side.label('side'),
                           players.c.weight.label('weight'),
                           teams.c.idx.label('slot'),
                           teams.c.sid.label('sid'),
                           formes.c.species.label('species'),
                           mf.c.prime.label('prime')])
                .select_from(join)
                .order_by(formes.c.species)
                .order_by(mf.c.prime.desc())).alias()

        combo_formes = sa.func.group_concat(join.c.species
                                            ).label('combined_formes')
        pretty = sa.case(species_lookup,
                         value=combo_formes,
                         else_='-' + combo_formes)

        query = (sa.select([join.c.bid,
                            join.c.side,
                            join.c.weight,
                            join.c.slot,
                            join.c.sid,
                            pretty.label('species')])
                 .select_from(join)
                 .group_by(join.c.bid,
                           join.c.side,
                           join.c.slot))
        return query.alias()

    def _remove_duplicates(self, team_members):
        """
        Prevent double-counting in usage stats for metagames without species
        clause by combining team members of the same species

        Args:
            team_members (sa.sql.expression.Alias) :
                the relevant weighted team members

        Returns:
            sa.sql.expression.Alias :
                the input table with duplicate team members combined
        """
        query = (sa.select([team_members.c.bid,
                            team_members.c.side,
                            team_members.c.weight,
                            sa.func.count(team_members.c.slot).label('count'),
                            team_members.c.species])
                 .select_from(team_members).group_by(team_members.c.bid,
                                                     team_members.c.side,
                                                     team_members.c.species))
        return query.alias()

    def get_usage_by_species(self, month, metagame, species_lookup,
                             baseline=1630.):
        team_members = self._remove_duplicates(
            self._weighted_team_members(
                self._weighted_players(
                    self._filtered_battles(month, metagame),
                    baseline),
                species_lookup))

        total = sa.func.sum(team_members.c.weight).label('sum')
        query = (sa.select([team_members.c.species,
                            total])
                 .select_from(team_members)
                 .group_by(team_members.c.species)
                 .order_by(total.desc()))
        return list(self.conn.execute(query))
