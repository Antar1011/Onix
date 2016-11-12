"""Interface for pulling data needed for report-generation"""
import abc

from future.utils import with_metaclass


class ReportingDAO(with_metaclass(abc.ABCMeta, object)):
    """
    Data Access Object for getting the raw data needed to produce reports

    Notes:
        The same filtering logic should be applied across all methods, that is,
        if it's policy to discard early forfeits for stat-counting, they should
        be discarded for battle-counting as well
    """

    @abc.abstractmethod
    def get_usage_by_species(self, month, metagame, species_lookup,
                             baseline=1630., min_turns=3):
        """
        Get usage counts by species

        Args:
            month (str) :
                the month to analyze
            metagame (str) :
                the sanitized name of the metagame
            species_lookup (dict) :
                mapping of species names or forme-concatenations to their
                display names. This is what handles things like determining
                whether megas are tiered together or separately or what counts
                as an "appearance-only" forme.
            baseline (:obj:`float`, optional) :
                the baseline to use for  skill_chance. Defaults to 1630.

                .. note ::
                   a baseline of zero corresponds to unweighted stats
            min_turns (:obj:`int`, optional) :
                don't count any battles fewer than this many turns in length.
                Defaults value is 3.

        Returns:
            :obj:`iterable` of :obj:`tuple` :
                weighted usage counts for each species, sorted from highest
                usage to lowest. The first value in each tuple is the Pokemon's
                display name, the second the weighted  count. If a species'
                display name is not specified (not in the `species_lookup`
                dictionary), then the display name will be given as the species'
                sanitized name, prepended with "-".

        """

    @abc.abstractmethod
    def get_number_of_battles(self, month, metagame, min_turns=3):
        """
        Get the number of battles

        Args:
            month (str) :
                the month to analyze
            metagame (str) :
                the sanitized name of the metagame
            min_turns (:obj:`int`, optional) :
                don't count any battles fewer than this many turns in length.
                Defaults value is 3.

        Returns:
            int :
                The number of battles in that metagame in that month
        """

    @abc.abstractmethod
    def get_total_weight(self, month, metagame, baseline=1630., min_turns=3):
        """
        Get the sum of weights

        Args:
            month (str) :
                the month to analyze
            metagame (str) :
                the sanitized name of the metagame
            baseline (:obj:`float`, optional) :
                the baseline to use for weighting. Defaults to 1630.

                .. note ::
                   a baseline of zero corresponds to unweighted stats
            min_turns (:obj:`int`, optional) :
                don't count any battles fewer than this many turns in length.
                Defaults value is 3.

        Returns:
            float :
                The sum of the weights for each team-instance for that month
                and metagame at the specified baseline
        """
