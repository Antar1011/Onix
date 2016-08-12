# Development Roadmap

This document lays out my plans for the development of Onix

## Milestones

### 0.1
"Proof of Concept" release with a complete functioning pipeline from logs to
stat reports for the most essential of analyses. This release must meet the
following requirements: 
  - Can produce usage statistics / rankings report for all non-mod tiers (so,
  yes Hackmons, no Gen V UU)
  - Can produce detiled moveset statistics, _sans_ checks & counters
  - Log reader supports extraction of movesets and battle info
      - processing the turn-by-turn battle logs not required at this point

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
 