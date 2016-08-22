"""Methods for generating various reports"""
from onix.reporting import dao


def generate_usage_stats(dao, formats, species_lookup, month, metagame,
                         baseline=1630.0):
    """Generate a usage stats report

    Args:
        dao (dao) :
            access object used to grab usage data
        formats (dict) :
            used for determining the rulesets that apply to the metagame.
            Scraped from Pokemon Showdown, with some significant post-processing
        species_lookup (dict) :
            mapping of sanitized species names to their display names
        month (str) :
                the month to analyze
        metagame (str) :
            the sanitized name of the metagame
        baseline (:obj:`float:, optional) :
            the baseline to use for  weighting. Defaults to 1630.
            .. note :
               a baseline of zero corresponds to unweighted stats

    Returns:
        str :
            the usage stats report, ready for printing to stdout or saving to
            file
    """
