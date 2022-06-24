import argparse
import configparser
import json
import os
import subprocess
from shlex import split as sh_split

from utils.remove_c_style_comments import comment_remover


def remove_comments(file):
    with open(file, "r+") as f:
        result = comment_remover(f.read())
        f.seek(0)
        f.write(result)
        f.truncate()


def setup_config(
        folder,
        endpoint,
        jacococli_jar,
        source_files,
        class_files,
        url
):
    config = configparser.ConfigParser()
    config.read("config.ini")
    config["DEFAULT"]["endpoint"] = json.dumps(endpoint)
    config["DEFAULT"]["jacococli_jar"] = str(jacococli_jar)
    config["DEFAULT"]["source_files"] = str(source_files)
    config["DEFAULT"]["class_files"] = str(class_files)
    config["DEFAULT"]["url"] = str(url)
    with open(os.path.join(folder, "config.ini"), "w") as config_file:
        config.write(config_file)


def standard_test(
        timesteps,
        episode_length,
        input_domain,
        sast_result,
        jacococli_jar,
        source_files,
        class_files,
        url,
        input_boundary=True,
        config_file="config.ini",
        timer=100,
):
    n_cpus = 1
    active_processes = 0
    processes = []
    # py = os.path.join(__file__, os.pardir, 'venv', 'bin', 'python')
    # py = os.path.abspath(py)
    py = os.popen('which python').read().replace('\n', '')
    script = os.path.abspath(os.path.join(__file__, os.pardir, 'test_java_program.py'))
    my_path = '.'
    with open(sast_result, 'r') as f:
        sast_result = json.load(f)
        for endpoint in sast_result:
            setup_config(
                folder=my_path,
                endpoint=endpoint,
                jacococli_jar=jacococli_jar,
                source_files=source_files,
                class_files=class_files,
                url=url
            )

            cmd = f'{py} {script} --config_path {my_path} --timesteps {timesteps} ' \
                  f'--input_boundary --input_domain {input_domain} ' \
                  f'--config_file {config_file} --timer {timer} --episode_length {episode_length}'
            active_processes += 1
            processes.append(subprocess.Popen(sh_split(cmd)))

            if active_processes == n_cpus:
                exit_codes = [p.wait() for p in processes]
                active_processes = 0
        if active_processes > 0:
            exit_codes = [p.wait() for p in processes]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--timesteps", type=int, required=True)
    parser.add_argument("--input_domain", type=int, required=True)
    parser.add_argument("--episode_length", type=int, required=True)
    parser.add_argument("--timer", type=int, required=True)
    parser.add_argument("--sast_result", type=str, required=True)
    parser.add_argument("--jacococli_jar", type=str, required=True)
    parser.add_argument("--source_files", type=str, required=True)
    parser.add_argument("--class_files", type=str, required=True)
    parser.add_argument("--url", type=str, required=True)

    args = parser.parse_args()
    timer = args.timer
    timesteps = args.timesteps
    input_domain = args.input_domain
    episode_length = args.episode_length
    sast_result = args.sast_result
    jacococli_jar = args.jacococli_jar
    source_files = args.source_files
    class_files = args.class_files
    url = args.url

    if os.path.exists('result/result.txt'):
        os.remove('result/result.txt')

    standard_test(
        timesteps,
        episode_length=episode_length,
        input_domain=input_domain,
        timer=timer,
        sast_result=sast_result,
        jacococli_jar=jacococli_jar,
        source_files=source_files,
        class_files=class_files,
        url=url
    )


if __name__ == "__main__":
    main()
