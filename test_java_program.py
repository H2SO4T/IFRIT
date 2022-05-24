import argparse
import os
import time
from stable_baselines3 import PPO
import java_tester
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
    env = java_tester.java_tester(
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
    # callback = TimerCallback(timer=timer)
    a = time.time()
    # model.learn(total_timesteps=timesteps, callback=callback)
    model.learn(total_timesteps=timesteps)
    tot_time = int((time.time() - a) / 60)

    # policy name
    model_name = f"ppo_ep_len:{episode_length}_input_domain:{input_domain}"
    model.save(model_name)


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
