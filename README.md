# PING
## **P**rolog **I**n the **N**etHack **G**ame

**PING** defines a Prolog knowledge base for a simple enviroment defined in [MiniHack](https://minihack.readthedocs.io/en/latest/).

The room is a 10x10 grid, with an enemy, a weapon, a trap and an apple. The task is to pick up the apple and eat it.

It uses the [PySwip](https://github.com/yuce/pyswip) package to integrate the Prolog KB and ask queries in Python scripts.

### Installation
This application requires MiniHack for the environment definition; it can be easily installed via [pypi](https://pypi.org/project/minihack/):
```bash
$ pip install minihack
```

For the reasoning process, it needs [SWI-Prolog](https://www.swi-prolog.org/) and [PySwip](https://github.com/yuce/pyswip).

### Trying it out

```bash
$ python main.py -h
usage: main.py [-h] [--width WIDTH] [--height HEIGHT] [--monster MONSTER] [--weapon WEAPON]
               [--trap TRAP] [--path_to_kb PATH_TO_KB] [--num_episodes NUM_EPISODES]
               [--max_steps MAX_STEPS] [--logging] [--fast_mode] [--save_gif] [--gif_path GIF_PATH]
               [--gif-duration GIF_DURATION]

optional arguments:
  -h, --help            show this help message and exit
  --width WIDTH         The width of the environment
  --height HEIGHT       The height of the environment
  --monster MONSTER     The type of monster present in the environment
  --weapon WEAPON       The weapon present in the environment
  --trap TRAP           The type of trap present in the environment
  --path_to_kb PATH_TO_KB
                        The path to the Prolog knowledge base
  --num_episodes NUM_EPISODES
                        The number of episodes to perform
  --max_steps MAX_STEPS
                        The maximum number of steps per episode
  --logging             Save the assertion made in Prolog
  --fast_mode           Print only summary information
  --save_gif            Save the episodes as gifs
  --gif_path GIF_PATH   Where to save the GIF of the episodes
  --gif-duration GIF_DURATION
                        The duration of each GIF image
```
