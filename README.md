# Ayberk's Humble Wordle Solver

[![](https://img.shields.io/badge/Ask%20me-anything-1abc9c.svg)](https://twitter.com/ayberkrants)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
![](http://unmaintained.tech/badge.svg)

This code might or might not work. No guarantees whatsoever. Use at your own risk. Licensed under
MPLv2, but it's _highly_ unlikely I'd be coming after you if you somehow find a way to monetize this
code. Oh also, if you do, please let me know so I can live the rest of my life with regret.

There's at least one bug that I know of, but obviously there probably are more than that, especially
since I did a big cleanup and didn't test the code thoroughly after that.


### How to run

`python3 wordle.py --help`

The most important argument is `game_mode`:
- `play`: In this mode you play against the computer. Good for practicing. This is the default mode.
- `solve`: In this mode the bot solves the puzzle for you. It gives you a guess word, you give it
back the feedback, i.e., which letters are green etc.
- `bot_play`: In this mode you basically become the observer. Useful for running simulations.

### How to inject your own solver

It should be fairly straightforward to use your own solver. The interface only has two methods and you can use the `WordleHelper` class as an example.

----
TODO:
- [ ] Run monte-carlo simulations to figure out best words/strategies
- [ ] Improve elimination by assigning scores to each word based on character frequency.
- [ ] WaaS: Wordle as a Service. Expose an API, because why not?
- [ ] Full automation: Go to game website, simulate an actual user by taking screenshots etc.
