import configparser
import os
import glob
import re
import subprocess
from shlex import split as sh_split
import test_c_program
import dist
from utils.remove_c_style_comments import comment_remover
import argparse


def remove_comments(file):
    with open(file, "r+") as f:
        result = comment_remover(f.read())
        f.seek(0)
        f.write(result)
        f.truncate()


def setup_config(
        folder, sourcecode_name, variables_space, branch_target_line, scanf_use, strings_use
):
    config = configparser.ConfigParser()
    config.read("config.ini")
    config["DEFAULT"]["main_folder"] = folder
    config["DEFAULT"]["strings_use"] = str(strings_use)
    config["DEFAULT"]["sourcecode_name"] = os.path.basename(sourcecode_name)
    config["DEFAULT"]["target_file"] = os.path.basename(sourcecode_name)
    config["DEFAULT"]["variables_space"] = str(variables_space)
    config["DEFAULT"]["branch_target_line"] = str(branch_target_line)
    config["DEFAULT"]["scanf"] = str(scanf_use)
    with open(os.path.join(folder, "config.ini"), "w") as config_file:
        config.write(config_file)


def search_c_files(curr_dir):
    c_files = glob.glob(f"{curr_dir}{os.sep}**/*.c", recursive=True)
    interesting_files = list()
    for c_file in c_files:
        if ".pre.c" not in c_file:
            with open(c_file, "r") as f:
                for line in f.readlines():
                    if line.find("int main(int argc,char *argv[])"):
                        interesting_files.append(c_file)
                        break
    interesting_files = sorted(interesting_files)
    if len(interesting_files) > 2:
        # this is the original without mutants
        fixed = interesting_files[0]
        # these are all the mutants
        buggy = interesting_files[1:]
    else:
        # this is the new version
        fixed = interesting_files[1]
        # this is the old one
        buggy = [interesting_files[0]]
    return buggy, fixed


def discover_var_space(fix):
    _max_args = 0
    max_args = 0
    int_args = 0
    string_args = 0
    with open(fix, "r") as file:
        for line in file.readlines():
            for arg in re.findall(r"(argv\[[0-9]+\])", line):
                temp_int = int(re.search(r"[0-9]+", arg).group())
                if temp_int > max_args:
                    max_args = temp_int
            if "scanf" in line:
                int_args = line.count("%d")
                string_args = line.count("%s")
                max_args = line.count("%")
            elif "fgets" in line:
                string_args = line.count("%s")
                max_args = line.count("%")
            elif "gets" in line:
                string_args = 1
                max_args = 1
    scanf_use = True if max_args else False
    strings_use = True if string_args else False
    target_function = "main"
    if not max_args and not _max_args:
        target_function = os.path.basename(fix).replace(".c", "")
        # the target is not the fucking main but in a function
    return max(max_args, max_args), scanf_use, strings_use, target_function


def standard_test(
        timesteps,
        episode_length,
        input_domain,
        input_boundary=True,
        config_file="config.ini",
        timer=100,
):
    n_cpus = 4
    active_processes = 0
    processes = []
    # py = os.path.join(__file__, os.pardir, 'venv', 'bin', 'python')
    # py = os.path.abspath(py)
    py = os.popen('which python').read().replace('\n', '')
    script = os.path.abspath(os.path.join(__file__, os.pardir, 'test_c_program.py'))
    for curr_dir in next(os.walk("programs"))[1]:
        my_path = os.path.join(os.getcwd(), "programs", curr_dir)
        if not os.path.isfile(f"{my_path}{os.sep}config_manual.ini"):
            buggy, fix = search_c_files(my_path)
            # this removes undesired comments
            remove_comments(fix)
            for bug in buggy:
                # this removes undesired comments
                remove_comments(bug)
                (
                    variables_space,
                    scanf_use,
                    strings_use,
                    target_function,
                ) = discover_var_space(bug)
                branch_target_line, _ = dist.compute_difference(
                    fixed=fix, buggy=bug, fun=target_function
                )
                setup_config(
                    folder=my_path,
                    sourcecode_name=fix,
                    variables_space=variables_space,
                    branch_target_line=branch_target_line,
                    scanf_use=scanf_use,
                    strings_use=strings_use,
                )
                cmd = f'{py} {script} --config_path {my_path} --timesteps {timesteps} ' \
                      f'--input_boundary --input_domain {input_domain} ' \
                      f'--config_file {config_file} --timer {timer} --episode_length {episode_length}'
                active_processes += 1
                processes.append(subprocess.Popen(sh_split(cmd)))
        else:
            cmd = f'{py} {script} --config_path {my_path} --timesteps {timesteps} ' \
                  f'--input_boundary --input_domain {input_domain} ' \
                  f'--config_file config_manual.ini --timer {timer} --episode_length {episode_length}'
            active_processes += 1
            processes.append(subprocess.Popen(sh_split(cmd)))
        if active_processes == n_cpus:
            exit_codes = [p.wait() for p in processes]
            active_processes = 0
    if active_processes > 0:
        exit_codes = [p.wait() for p in processes]


def mutant_test(timesteps, timer, config_file="config.ini"):
    seed = 30
    for curr_dir in next(os.walk("programs"))[1]:
        my_path = os.path.join(os.getcwd(), "programs", curr_dir)
        if not os.path.isfile(f"{my_path}{os.sep}config_manual.ini"):
            mutants, original = search_c_files(my_path)
            # testing the original
            for mutant in mutants:
                # testing the original program
                (variables_space, scanf_use, strings_use, target_function,) = discover_var_space(original)

                branch_target_line, _ = dist.compute_difference(
                    fixed=original, buggy=mutant, fun=target_function
                )
                setup_config(folder=my_path, sourcecode_name=original, variables_space=variables_space,
                             branch_target_line=branch_target_line, scanf_use=scanf_use, strings_use=strings_use, )

                # The trace generated by the original program
                first_trace = test_c_program.train_mutants(my_path, seed=seed, timesteps=timesteps,
                                                           config_file=config_file, timer=timer)

                setup_config(folder=my_path, sourcecode_name=mutant, variables_space=variables_space,
                             branch_target_line=branch_target_line, scanf_use=scanf_use, strings_use=strings_use, )

                # The trace generated by the mutant
                second_trace = test_c_program.train_mutants(my_path, seed=seed, timesteps=timesteps,
                                                            config_file=config_file, timer=timer)

                trace = "Same"
                for i in range(min(len(first_trace), len(second_trace))):
                    if first_trace[i] != second_trace[i]:
                        trace = "Different"
                        break
                with open("mutant_traces.csv", "a+") as f:
                    f.write(
                        f"{os.path.basename(original)}; {os.path.basename(mutant)}; {trace}\n"
                    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--train_type", type=int, required=True)
    parser.add_argument("--timesteps", type=int, required=True)
    parser.add_argument("--input_domain", type=int, required=True)
    parser.add_argument("--episode_length", type=int, required=True)
    parser.add_argument("--timer", type=int, required=True)
    args = parser.parse_args()
    timer = args.timer
    train_type = args.train_type
    if train_type < 0 or train_type > 1:
        raise Exception("train_type must be a value between 0 and 1")
    timesteps = args.timesteps
    input_domain = args.input_domain
    episode_length = args.episode_length

    if train_type == 0:
        standard_test(timesteps, episode_length=episode_length, input_domain=input_domain, timer=timer,)

    elif train_type == 1:
        mutant_test(timesteps, timer=60)


if __name__ == "__main__":
    main()
