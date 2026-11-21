card.svg is generated. Do not edit it by hand.

To change anything on the card, edit config.json and commit it. The GitHub Action
rebuilds card.svg right away and then again every day, which keeps "uptime" counting.

To rebuild on your own machine:  python3 scripts/build.py   (needs only Python 3)

To make repos / commits update by themselves, set "repos": "auto" and/or
"commits": "auto" in config.json.

To change the portrait, replace scripts/assets/portrait.txt (plain ASCII, one line per row).
