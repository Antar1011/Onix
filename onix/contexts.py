"""Object, factories and utilities for bundling and accessing resources"""
import json

from future.utils import iteritems

from onix import scrapers
import onix.utilities as ut


class Context(object):
    """
    Grouping of resources and static lookups, bundled together for ease of
    access.

    Notes:
        Be careful when using this in a multiprocessor context, as transmitting
        all the lookups to each worker process is a metric ton of overhead when
        it's extremely unlikely that each worker needs *every single* resource.

    Args:
        **resources : the resources to be bundled. Note that there's no need to
            limit one's self to the attributes listed below.

    Attributes:
        aliases (dict) : the data encoded in `aliases.js` on PS. The keys are
            the alternate names, the values are the correct names.
        formats (dict) : the data encoded in `formats.js` on PS, post-processed
            for increased utility. The keys are the sanitized format names. The
            values are the various configurations and metadata for the metagame.
        formats_data (dict) : the data encoded in `formats-data.js` on PS. The
            keys are the species / forme names, the values contain information
            like current tier and random battle move pool
        items (dict) : the data encoded in `items.js` on PS. The keys are
            sanitized item names, the values associated metadata including, for
            mega stones, which Pokemon it mega-evolves.
        moves (dict) : the data encoded in `moves.js` on PS. The keys are
            sanitized move names, the values the associated metadata including
            move type and base power
        pokedex (dict) : the data encoded in `pokedex.js` on PS. The keys are
            the species / forme names. The values contain information like base
            stats and valid abilities.
        accessible_formes (dict) : a mapping of species and formes to the routes
            they have to access other formes.
        natures (dict) : The keys are the sanitized nature names, the values
            the associated metadata, such as which stat gets boosted and which
            gets lowered.
        species_lookup (dict) : mapping of sanitized species names or
            forme-concatenations (e.g. "sceptile,sceptilemega") to their display
            names. This is what handles things like determing whether megas
            are tiered together or separately or what counts as an
            "appearance-only" forme.
        sanitizer (onix.utilities.Sanitizer) : the sanitizer to use to normalize
            data and model objedts.
    """

    def __init__(self, **resources):

        self.aliases = None
        self.formats = None
        self.formats_data = None
        self.items = None
        self.moves = None
        self.pokedex = None
        self.accessible_formes = None
        self.natures = None
        self.species_lookup = None
        self.sanitizer = None

        for name, resource in iteritems(resources):
            setattr(self, name, resource)


class ResourceMissingError(Exception):
    """Raised if an expected resource is not present in a given context

    Args:
        resource (str) : the name of the missing resource
    """

    def __init__(self, resource):
        msg = 'Context does not include the "{0}" resource'.format(resource)
        super(ResourceMissingError, self).__init__(msg)


def require(context, *resources):
    """
    Validate that the specified ``Context`` has all the specified resources

    Args:
        context (Context) : the context to validate
        *resources : the names of the attributes to require

    Raises:
        ResourceMissingError: if a required resource is missing from the
            context
    """

    for resource in resources:
        if hasattr(context, resource):
            if getattr(context, resource) is not None:
                continue
        raise ResourceMissingError(resource)


def get_standard_context(force_refresh=False):
    """
    Create a ``Context`` with all the standard (current generation, non-mod)
    resources.

    Args:
        force_refresh (:obj:`bool`, optional) : By default, this method will
            try to load the resources from the local file cache. Set to False
            to force it to freshly download scrape the Pokemon Showdown data.

    Returns:
        Context :
            A context with all the standard resources
    """

    psdata = dict(aliases=None, formats=None, formats_data=None, items=None,
                  moves=None, pokedex=None)

    if not force_refresh:
        for resource in psdata.keys():
            try:
                psdata[resource] = json.load(open('.psdata/{0}.json'
                                                  .format(resource)))
            except IOError:
                pass

    if psdata['aliases'] is None:
        psdata['aliases'] = scrapers.scrape_battle_aliases()
    if psdata['formats'] is None:
        psdata['formats'] = scrapers.scrape_formats()
    if psdata['formats_data'] is None:
        psdata['formats_data'] = scrapers.scrape_battle_formats_data()
    if psdata['items'] is None:
        psdata['items'] = scrapers.scrape_battle_items()
    if psdata['moves'] is None:
        psdata['moves'] = scrapers.scrape_battle_movedex()
    if psdata['pokedex'] is None:
        psdata['pokedex'] = scrapers.scrape_battle_pokedex()

    return Context(accessible_formes=ut.load_accessible_formes(),
                   natures=ut.load_natures(),
                   species_lookup=ut.load_species_lookup(),
                   sanitizer=ut.Sanitizer(psdata['pokedex'],
                                          psdata['aliases']),
                   **psdata)





