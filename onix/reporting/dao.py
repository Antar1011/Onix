"""Interface for pulling data needed for report-generation"""
import abc

import six


class ReportingDAO(six.with_metaclass(abc.ABCMeta, object)):
    """Data Access Object for getting the raw data needed to produce reports"""

    @abc.abstractmethod
    def get_usage_by_species(self, month, metagame, baseline=1630.0):
        """
        Get usage counts  by species

        Args:
            month (str) :
                the month to analyze
            metagame (str) :
                the sanitized name of the metagame
            baseline (:obj:`float:, optional) :
                the baseline to use for  weighting. Defaults to 1630.
                .. note :
                   a baseline of zero corresponds to unweighted stats

        Returns:
            :obj:`dict` of :obj:`str` to :obj:`float` :
                The usage numbers (summed weights) for each species. Species are
                represented as stringified lists of all forme names (so a Mega
                Ampharos will be represented as "ampharos,ampharosmega").
                It is the responsibility of the report-generator to map these to
                display names and to combine counts for equivalent formes. There
                will be one entry for ``None`` representing empty team slots.
        """

    @abc.abstractmethod
    def get_number_of_battles(self, month, metagame):
        """
        Get the number of battles

        Args:
            month (str) :
                the month to analyze
            metagame (str) :
                the sanitized name of the metagame

        Returns:
            int :
                The number of battles in that metagame in that month

                .. note :
                    The same filtering logic should be applied to this method as
                    to `get_usage_by_species`, that is, if it's policy to
                    discard early forfeits for stat-counting, they should be
                    discarded for battle-counting as well
        """