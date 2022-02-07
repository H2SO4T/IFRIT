import argparse
import os
import time
from stable_baselines3 import PPO
import c_tester
from utils.TimeFeatureWrapper import TimeFeatureWrapper
from stable_baselines3.ppo.policies import MlpPolicy
import matplotlib.pyplot as plt
from utils.timer_callback import TimerCallback
from utils.tests import uniform_comparison, diversity_strings
from stable_baselines3.common.monitor import Monitor


def print_input_curve(input_curve, config_path):
    x = [t for t in range(len(input_curve))]
    plt.plot(x, input_curve)
    plt.xlabel("calls to the program")
    plt.ylabel("number of correct inputs")
    plt.savefig(os.path.basename(config_path))
    plt.close()


def train(
        config_path,
        timesteps=6000,
        input_boundary=True,
        input_domain=100,
        config_file="config.ini",
        timer=60,
        episode_length=1000,
):
    curr_path = os.getcwd()
    # creating the env
    env = c_tester.c_tester(
        os.path.join(config_path, config_file),
        input_boundary=input_boundary,
        input_domain=input_domain,
        episode_length=episode_length,
    )
    # wrapping it
    name = env.target_file
    env = TimeFeatureWrapper(env)
    # creating a directory for log files
    tensorboard_dir = f"{config_path}{os.sep}log"
    os.makedirs(tensorboard_dir, exist_ok=True)

    env = Monitor(env, filename=tensorboard_dir)
    # env = make_vec_env(lambda: env, n_envs=4)

    model = PPO(MlpPolicy, env, verbose=1, tensorboard_log=tensorboard_dir)
    callback = TimerCallback(timer=timer)
    a = time.time()
    model.learn(total_timesteps=timesteps, callback=callback)
    tot_time = int((time.time() - a) / 60)

    # policy name
    model_name = f"ppo_ep_len:{episode_length}_input_domain:{input_domain}"
    model.save(model_name)
    # reloading the policy
    diversity_training = set(env.diversity_inputs)
    env.diversity_inputs = set()

    model = PPO.load(model_name)
    obs = env.reset()
    for i in range(episode_length):
        action, _states = model.predict(obs)
        _, rewards, _, _ = env.step(action)

    # taking all inputs coming from the learned policy
    policy_diversity = set(env.diversity_inputs)
    policy_diversity = policy_diversity.union(diversity_training)
    valid_inputs = [list(x) for x in policy_diversity]
    valid_inputs.sort()

    # back to the future
    os.chdir(curr_path)
    # print_input_curve(env.input_curve, config_path)

    if not env.strings_use:
        result = uniform_comparison(
            valid_inputs[: min(episode_length, len(valid_inputs))]
        )
    else:
        result = diversity_strings(valid_inputs)

    os.makedirs('results', exist_ok=True)
    dir_program = name.replace('.c', '')
    os.makedirs(f'results{os.sep}{dir_program}', exist_ok=True)

    # summary of the programs execution
    with open(f'results{os.sep}summary.csv', 'a+') as f:
        f.write(
            f'name: {name}; test suit dimension:{len(valid_inputs)}; episode length: {episode_length};'
            f' input_domain:{input_domain}; diverse: {result}; exec_time {tot_time}\n'
        )
    i = 0
    # valid input
    while True:
        if not os.path.isfile(f'results{os.sep}{dir_program}{os.sep}input_generated_{i}_{dir_program}.txt'):
            with open(f'results{os.sep}{dir_program}{os.sep}input_generated_{i}_{name}.txt', 'w') as f:
                for line in valid_inputs:
                    f.write(f'{str(line)[1:-1]}\n')
            break
        i += 1

        '''except:
            with open(f'results{os.sep}results.csv', 'a+') as f:
                f.write(
                    f"name: {name}; test suit dimension:{len(valid_inputs)}; episode length: {episode_length};"
                    f" input_domain:{input_domain}; diverse: False; exec_time{tot_time}\n"
        )'''


def train_mutants(config_path, seed, timesteps=500, config_file="config.ini", timer=60):
    curr_path = os.getcwd()
    env = c_tester.c_tester(
        os.path.join(config_path, config_file), mutation_trace=True, episode_length=1000
    )
    env = TimeFeatureWrapper(env)
    model = PPO(MlpPolicy, env, verbose=2, seed=seed)
    callback = TimerCallback(timer=timer)
    model.learn(total_timesteps=timesteps, callback=callback)
    diversity = len(env.diversity_inputs)
    # back to the future
    os.chdir(curr_path)
    return env.output_trace


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config_path", type=str, required=True)
    parser.add_argument("--timesteps", type=int, required=True)
    parser.add_argument('--input_boundary', default=False, action='store_true')
    parser.add_argument("--input_domain", type=int, required=True)
    parser.add_argument("--config_file", type=str, required=True)
    parser.add_argument("--timer", type=int, required=True)
    parser.add_argument("--episode_length", type=int, required=True)
    args = parser.parse_args()

    config_path = args.config_path
    timesteps = args.timesteps
    input_boundary = args.input_boundary
    input_domain = args.input_domain
    config_file = args.config_file
    timer = args.timer
    episode_length = args.episode_length

    train(
        config_path=config_path,
        timesteps=timesteps,
        input_boundary=input_boundary,
        input_domain=input_domain,
        config_file=config_file,
        timer=timer,
        episode_length=episode_length,
    )


if __name__ == '__main__':
    main()
