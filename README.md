# Smogon-Usage-Stats: Rewrite
When I started this project, I was a grad student who'd only ever written academic code (where if it runs, no one really cares what it looks like or how it's written). I used this project to teach myself Python, and I knew not one iota of the principles of good software development. Five years later, I have grown so much as a programmer, a software developer and a data scientist, and frankly, I'm unhappy with the status of this codebase. Yes, the scripts work (for the most part), and keeping everything running has so far not been too onerous, but when I look at this repo, and I just feel _embarrassed_. I can do better. And I feel that I owe it to myself _to_ do better.

Just as I wrote the original Smogon Usage stats scripts to learn how to code Python, I'm now going to perform a complete rewrite as an opportunity to learn how to code Python _well_. That means:
  * adhering to PEP 8 and other Python best-practices
  * writing modular, reusable, easy-to-maintain code
  * writing covering tests that ensure robust performance and easy troubleshooting

None of this is likely to imporve performance significantly, but I also have plans to write versions of the scripts that leverage databases (ideally I'll have both an RMDBS (MySQL) and a NoSQL (MongoDB) implementation) that should increase performance dramatically, meaning improved time-to-stats and possibly an API for performing deep analyses that go beyond the detailed moveset stats.
