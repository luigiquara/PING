from minihack import LevelGenerator
from minihack import RewardManager

def create_level(width:int, height:int,
                 monster:str = 'kobold', trap:str = 'falling rock',
                 weapon='battle-axe'):
    lvl = LevelGenerator(w=width, h=height)
    lvl.add_monster(name=monster)
    lvl.add_trap(name=trap)
    lvl.add_object(name='apple', symbol='%')
    lvl.add_object(name=weapon, symbol=')')

    return lvl.get_des()

def define_reward(monster: str = 'kobold'):
    reward_manager = RewardManager()

    reward_manager.add_eat_event(name='apple', reward=2, terminal_sufficient=True, terminal_required=True)
    reward_manager.add_kill_event(name=monster, reward=1, terminal_required=False, )

    return reward_manager