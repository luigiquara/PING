import os
import shutil
import argparse
import gym
import minihack
from pyswip import Prolog
from env_definition import create_level, define_reward

def print_screen_descriptions(obs):
    for i in range(21):
        for j in range(79):
            if not (obs['screen_descriptions'][i][j] == 0).all():
                sample = bytes(obs['screen_descriptions'][i][j]).decode('utf-8').rstrip('\x00')
                if sample == 'floor of a room': sample = 'F'
                print(sample, end = ' ')
        print()

def log(to_assert):
    with open('log', 'a') as fp:
        fp.write(to_assert+'\n')

# Process observation and assert to Prolog
# Process screen_descriptions to get positions
def process_map(screen_descriptions, monster, prolog, logging):
    # Forget everything from before
    # Those information could be obsolete
    to_retract = 'position(_,_,_,_)'
    prolog.retractall(to_retract)

    for i in range(21):
        for j in range(79):
            if not (screen_descriptions[i][j] == 0).all():
                object = bytes(screen_descriptions[i][j]).decode('utf-8').rstrip('\x00')
                    
                if 'apple' in object:
                    # print(f'Found apple at [{i},{j}]')
                    to_assert = f'position(comestible, apple, {i}, {j})'
                    prolog.asserta(to_assert)
                    to_retract += '\n' + to_assert

                elif object == monster:
                    # print(f'Found monster at [{i},{j}]')
                    to_assert = f'position(enemy, {monster.replace(" ","")}, {i}, {j})'
                    prolog.asserta(to_assert)
                    to_retract += '\n' + to_assert

                elif 'corpse' in object:
                    # print(f'Found trap at [{i},{j}]')
                    to_assert = f'position(trap, _, {i}, {j})'
                    prolog.asserta(to_assert)
                    to_retract += '\n' + to_assert

                elif 'sword' in object:
                    # print(f'Found weapon at [{i},{j}]')
                    to_assert = f'position(weapon, tsurugi, {i}, {j})'
                    prolog.asserta(to_assert)
                    to_retract += '\n' + to_assert

    if logging: log(to_retract)

def process_inv(inv_strs, prolog, logging):
    # Forget info from before
    # Possibly obsolete
    to_retract = 'wields_weapon(_,_)'
    to_retract += '\n' + 'has(agent,_,_)'
    prolog.retractall(to_retract.split('\n')[0])
    prolog.retractall(to_retract.split('\n')[1])

    # Process inv_strs to get the weapon in hand
    for object in inv_strs:
        object = bytes(object).decode('utf-8').rstrip('\x00')

        if 'weapon in hand' in object:
            # the actual name of the weapon is in position 2
            weapon = object.split()[2]
            # print(f'Weapon wielded: {weapon}')
            to_assert = f'wields_weapon(agent, {weapon})'
            prolog.asserta(to_assert)
            to_retract += '\n' + to_assert

        if 'apple' in object:
            # print('The agent has the apple!')
            to_assert = 'has(agent, comestible, apple)'
            prolog.asserta(to_assert)
            to_retract += '\n' + to_assert

    if logging: log(to_retract)

# Process blstats for agent position and health
# X and Y of the agent are in position 0 and 1
# Current health and maximum health are in position 10 and 11
def process_blstats(blstats, prolog, logging):
    # Forget previous info
    to_retract = 'position(agent,_,_,_)'
    to_retract += '\n' + 'health(_)'
    prolog.retractall(to_retract.split('\n')[0])
    prolog.retractall(to_retract.split('\n')[1])

    # print(f'Agent at [{blstats[1]},{blstats[0]}]')
    to_assert = f'position(agent, _, {blstats[1]}, {blstats[0]})'
    prolog.asserta(to_assert)
    to_retract += '\n' + to_assert

    health_percentage = int(blstats[10]/blstats[11] * 100)
    to_assert = f'health({health_percentage})'
    prolog.asserta(to_assert)
    to_retract += '\n' + to_assert

    if logging: log(to_retract) 

def process_message(message, prolog, logging):
    message = bytes(message).decode('utf-8').rstrip('\x00')

    to_retract = ''
    to_assert = None
    if 'You see here' in message:
        if 'apple' in message:
            to_assert = 'stepping_on(agent, comestible, apple)'

        if 'sword' in message:
            to_assert = 'stepping_on(agent, weapon, tsurugi)'

    for m in message.split('.'):
        if 'picks' in m:
            if 'apple' in m:
                print('The enemy took your apple!')
                print(message)

    if to_assert:
        prolog.asserta(to_assert)
        to_retract += '\n' + to_assert
    if logging: log(to_retract) 


def perform_action(action, env):
    if action == 'eat': 
        action_id = 29
        # print(f'Action performed: {repr(env.actions[action_id])}')
        obs, _, _, _ = env.step(action_id)
        # Example message:
        # What do you want to eat?[g or *]
        message = bytes(obs['message']).decode('utf-8').rstrip('\x00')
        food_char = message.split('[')[1][0] # Because of the way the message in NetHack works
        action_id = env.actions.index(ord(food_char))

    elif action == 'pick': action_id = 49
    elif action == 'wield': action_id = 78

    # Movement/Attack/Run/Get_To_Weapon actions
    # in the end, they all are movement in a direction
    elif 'northeast' in action: action_id = 4
    elif 'southeast' in action: action_id = 5
    elif 'southwest' in action: action_id = 6
    elif 'northwest' in action: action_id = 7
    elif 'north' in action: action_id = 0
    elif 'east' in action: action_id = 1
    elif 'south' in action: action_id = 2
    elif 'west' in action: action_id = 3

    # print(f'Action performed: {repr(env.actions[action_id])}')
    obs, reward, done, info = env.step(action_id)
    return obs, reward, done, info
     

def main(width, height, monster, weapon, trap, path_to_kb, num_episodes,
         max_steps, logging, fast_mode, save_gif, gif_path, gif_duration):
    # Environment definition
    des_file = create_level(width=width, height=height, monster=monster, weapon=weapon, trap=trap)
    reward_manager = define_reward(monster=monster)

    env = gym.make('MiniHack-Skill-Custom-v0', character="sam-hum-neu-mal", observation_keys=('screen_descriptions','inv_strs','blstats','message','pixel_crop'),
                   des_file=des_file, reward_manager=reward_manager)

    # Prolog engine initialization
    prolog = Prolog()
    prolog.consult(path_to_kb)

    if save_gif:
        import PIL.Image
        import tempfile
        import glob
        # Temporary directory to store screenshots
        tmpdir = tempfile.mkdtemp()

    mean_return = 0.0
    for episode in range(num_episodes):
        steps = 0
        reward = 0.0
        mean_reward = 0.0

        obs = env.reset()
        if not fast_mode:
            env.render()
            print_screen_descriptions(obs)
        done = False

        if not fast_mode: input('Press a key to start the game!')

        # Main loop
        # Get the observation from the env 
        # Assert the facts in the kb 
        # Run the inference and get the action to perform
        # Apply the action in the environment
        for _ in range(max_steps):
            # Process the observation
            process_map(obs['screen_descriptions'], monster, prolog, logging)
            process_inv(obs['inv_strs'], prolog, logging)
            process_blstats(obs['blstats'], prolog, logging)
            process_message(obs['message'], prolog, logging)

            if save_gif:
                obs_image = PIL.Image.fromarray(obs['pixel_crop'])
                obs_image.save(os.path.join(tmpdir, f'e_{episode}_s_{steps}.png'))

            # Query Prolog
            # Get the first answer from Prolog -> the top-priority action
            try:
                action = list(prolog.query('action(X)'))[0]
                action = action['X']
                if not fast_mode: print(f'Current action from Prolog: {action}')
            except Exception as e:
                action = None

            # Perform the action in the environment
            if action:
                obs, reward, done, info = perform_action(action, env)
                if not fast_mode: env.render()
                if logging: log('New step \n')
            else: break

            steps += 1
            mean_reward = (reward - mean_reward) / steps

            if done: break
            if not fast_mode: input('Waiting for a key to go on...')

        # Print information about the ended episode
        print(f'Episode {episode} - {steps} steps')
        print(f'End status: {info["end_status"].name}')
        print(f'Final reward: {reward}')
        print(f'Mean reward: {mean_reward}')

        mean_return += (mean_reward * steps) / num_episodes

        obs = env.reset()
        prolog.retractall('stepping_on(agent,_,_)')
        if logging: log(f'Ended Episode {episode}\nStarting episode {episode+1}\n')

    # When all the episodes are done
    if save_gif:
    # Make the GIF and delete the temporary directory
        png_files = glob.glob(os.path.join(tmpdir, "e_*_s_*.png"))
        png_files.sort(key=os.path.getmtime)

        img, *imgs = [PIL.Image.open(f) for f in png_files]
        img.save(
            fp=gif_path,
            format="GIF",
            append_images=imgs,
            save_all=True,
            duration=gif_duration,
            loop=0,
        )
        shutil.rmtree(tmpdir)

        print("Saving replay GIF at {}".format(os.path.abspath(gif_path)))

    print(f'After {num_episodes} episodes, mean return is {mean_return}')
    

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--width',
        dest='width',
        type=int,
        default=10,
        help='The width of the environment'
    )
    parser.add_argument(
        '--height',
        dest='height',
        type=int,
        default=10,
        help='The height of the environment'
    )
    parser.add_argument(
        '--monster',
        dest='monster',
        type=str,
        default='kobold',
        help='The type of monster present in the environment'
    )
    parser.add_argument(
        '--weapon',
        dest='weapon',
        type=str,
        default='tsurugi',
        help='The weapon present in the environment'
    )
    parser.add_argument(
        '--trap',
        dest='trap',
        type=str,
        default='falling rock',
        help='The type of trap present in the environment'
    )
    parser.add_argument(
        '--path_to_kb',
        type=str,
        default='nethack_kb.pl',
        help='The path to the Prolog knowledge base'
    )
    parser.add_argument(
        '--num_episodes',
        type=int,
        default=5,
        help='The number of episodes to perform'
    )
    parser.add_argument(
        '--max_steps',
        type=int,
        default=30,
        help='The maximum number of steps per episode'
    )
    parser.add_argument(
        '--logging',
        action='store_true',
        dest='logging',
        help='Save the assertion made in Prolog' 
    )
    parser.add_argument(
        '--fast_mode',
        action='store_true',
        help='Print only summary information'
    )
    parser.add_argument(
        '--save_gif',
        action='store_true',
        help='Save the episodes as gifs'
    )
    parser.add_argument(
        '--gif_path',
        type=str,
        default='replay.gif',
        help='Where to save the GIF of the episodes'
    )
    parser.add_argument(
        '--gif-duration',
        type=int,
        default=300,
        help='The duration of each GIF image'
    )
    flags = parser.parse_args()
    main(**vars(flags))