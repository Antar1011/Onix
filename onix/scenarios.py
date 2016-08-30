"""Object, factories and utilties for bundling and accessing resources"""

import six


class Scenario(object):
    """
    Grouping of resources and static lookups, bundled together for ease of
    access.

    Notes:
        Be careful when using this in a multiprocessor context, as transmitting
        all the lookups to each worker process is a metric ton of overhead when
        it's extremely unlikely that each worker needs *every single* resource.

    Args:
        **resources (dict) : the dictionary of resources to be bundled together.
            There's no need to limit one's self to the attributes listed below.

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
            data and DTOs.
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

        for name, resource in six.iteritems(resources):
            setattr(self, name, resource)
