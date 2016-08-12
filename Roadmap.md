# Development Roadmap

This document lays out my plans for the development of Onix

## Milestones

### 1.0
At this point, Onix will be considered fully usable, and a system built on Onix
will officially replace the
[Smogon-Usage-Stats](https://github.com/Antar1011/Smogon-Usage-Stats) scripts in
 "production." This release must meet the following requirements:
  - Replicates or replaces the full suite of analyses present in the existing
  Smogon Usage Stats, namely:
    - Usage statistics / rankings
    - Detailed moveset statistics
        - Including checks / counters and teammate stats
    - Metagame analyses
    - Lead Stats
    - Detailed monotype statistics
  - Supports the following new analyses, not present in the current Smogon
  Usage Stats suite
    - Lead and check / counter stats for Doubles / Triples tiers
    - Support for non-standard metagames
        - Previous generations
        - Seasonal tiers
    - Move usage statistics
  - Supports a public API for deep queries (_e.g._ "What fraction of Serperior
  with ability Contrary run Leaf Storm?" and "What's the most common Pokemon on
  teams with both Landorus and Charizard-Mega-X?")
  - Supports researcher access to anonymized data sources (that is, backed by
  a database that provides fine-grain access control)
 