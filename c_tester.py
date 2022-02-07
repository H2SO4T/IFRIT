import glob
import os
import subprocess
from shlex import split as sh_split
import gym
import numpy as np
import configparser
import operator
import ctypes
from gcovr import __main__ as gcov


def to_string(tree):
    temp = ''
    for code_line in tree[1][0][0][0][1]:
        temp += str(code_line.items())
    return temp


class c_tester(gym.Env):

    def __init__(self, config_file, mutation_trace=False, input_boundary=True, input_domain=6000,
                 episode_length=15_000):
        super(c_tester, self).__init__()
        self.ops = {
            '+': operator.add,
            '-': operator.sub,
            '*': operator.mul,
            '/': operator.truediv,
            '%': operator.mod,
            '^': operator.xor
        }

        self.c_types = {
            'int': ctypes.c_int,
            'float': ctypes.c_float,
            'double': ctypes.c_double,
            'str': ctypes.c_char_p,
        }

        self.index = 0
        self.config_file = os.path.basename(config_file)
        self.alphabet = 'abcdefghijklmnopqrstuvwxyz ;(){}[]1234567890?:.+-*/&|%"~'
        # in case a certain input breaks the program
        self.timeout_inputs = set()

        self.input_boundary = input_boundary
        # these are used when you want to collect the output coming from the program execution
        self.mutation_trace = mutation_trace
        self.output_trace = list()

        # diversity_inputs collects all the different input generated during the training phase
        self.diversity_inputs = set()
        # saving all inputs in an episode
        self.successes = set()
        # collects all input generated during training
        self.variables_vector_history = list()
        self.config = configparser.ConfigParser()
        self.config.read(config_file)
        # starting parse
        self.variables_space = int(self.config['DEFAULT']['variables_space'])
        # these are used when you want to compute diversity
        self.input_domain = input_domain

        self.string_max_len = 5
        self.strings_use = False if self.config['DEFAULT']['strings_use'] == 'False' else True
        self.read_from_file = False if self.config['DEFAULT']['read_from_file'] == 'False' else True
        # branch target is at line:
        self.branch_target_line = int(self.config['DEFAULT']['branch_target_line'])

        if self.config['DEFAULT']['arg_order'] != 'none':
            self.variables_types = [elem for elem in self.config['DEFAULT']['arg_order'].split()]
        else:
            self.variables_types = 'str' if self.strings_use else 'int'

        self.target_line = -1
        self.offset = 0
        # it contains the branch number and the line
        self.branches = dict()
        # initializing the variable vector
        if type(self.variables_types) != list:
            if self.variables_types == 'str':
                self.variables_vector = [''] * self.variables_space
            elif self.variables_types == 'int':
                self.variables_vector = [0] * self.variables_space
        else:
            self.variables_vector = list()
            for elem_type in self.variables_types:
                value = 0 if (elem_type == 'int' or elem_type == 'double') else ''
                self.variables_vector.append(value)
        self.input_curve = [0]
        self.template_variables_vector = self.variables_vector[:]
        # steps
        self.steps = 0
        self._max_steps = episode_length
        self.scale_factors = [int(elem) for elem in self.config['DEFAULT']['scale_factors'].split()]
        self.operators_space = dict()
        counter = 0
        for actual_operator in self.config['DEFAULT']['operators'].split():
            self.operators_space[counter] = self.ops[actual_operator]
            counter += 1
        # main folder
        self.path = self.config['DEFAULT']['main_folder']
        # name of the compiled program
        self.executable = self.config['DEFAULT']['executable_name']
        self.scanf = False if self.config['DEFAULT']['scanf'] == 'False' else True
        self.target_file = self.config['DEFAULT']['target_file']
        # source code name
        self.source_code_name = self.config['DEFAULT']['sourcecode_name']
        if '.c' not in self.source_code_name:
            self.source_code_name += '.c'
        self.file_gcno = self.source_code_name.replace('.c', '.gcno')
        self.file_gcda = self.source_code_name.replace('.c', '.gcda')
        # changing dir for gcov tool.
        os.chdir(self.path)
        try:
            os.remove(self.file_gcno)
        except:
            pass
        try:
            os.remove(self.file_gcda)
        except:
            pass
        # compiling the program
        self.target_function = self.config['DEFAULT']['target_function']
        if self.target_function == 'main':
            compile_command = sh_split(f'gcc -fprofile-arcs -ftest-coverage -O3 {self.source_code_name}')
            self.exec_command = f'./{self.executable}'
            subprocess.call(compile_command)
            self.call_program = self.call_compiled_program
        else:
            # To maximize speed we compile the c code as a library
            compile_command = sh_split(f'gcc -fprofile-arcs -ftest-coverage -O3 -fPIC -shared -o my_lib.so '
                                       f'{self.source_code_name}')
            subprocess.call(compile_command)
            # Loading library
            self.LP_c_char = ctypes.POINTER(ctypes.c_char)
            self.LP_LP_c_char = ctypes.POINTER(self.LP_c_char)
            self.library = ctypes.CDLL('my_lib.so')
            self.library_function = getattr(self.library, self.target_function)
            self.call_program = self.call_library_program

        self.compute_target_line()
        self.observation = np.array([])
        # launching the program for the first time to determine the observation space
        self.step([0, 0, 0])
        # self.observation = self.get_observation(root)
        self.N_OBSERVATIONS = len(self.observation)
        if self.strings_use:
            self.action_space = gym.spaces.MultiDiscrete([self.variables_space, len(self.alphabet),
                                                          len(self.operators_space)])
        else:
            self.action_space = gym.spaces.MultiDiscrete([self.variables_space, len(self.scale_factors),
                                                          len(self.operators_space)])
        self.observation_space = gym.spaces.Box(low=-input_domain, high=input_domain,
                                                shape=(self.N_OBSERVATIONS,))

    def get_observation(self, root):
        observation = np.array([])
        for key, item in self.branches.items():
            single_observation = int(root[1][0][0][self.index][1][item['line_in_xml_file']].items()[1][1])
            observation = np.append(observation, [single_observation])

        for element in self.variables_vector:
            if type(element) == str:
                pos = ''
                for letter in element:
                    pos += str(self.alphabet.find(str(letter)))
                pos = 0 if pos == '' else pos
                observation = np.append(observation, int(pos))
            else:
                observation = np.append(observation, element)
        return observation

    def step(self, action):
        self.compute_variables_vector(action)
        # print(self.variables_vector)
        self.call_program()
        # this command calls the gcov program
        tree = gcov.main(['-r', '.', '--xml-pretty'])
        # computing the observation
        self.observation = self.get_observation(tree)
        reward, done = self.compute_reward()
        self.steps += 1
        # self.monitor_training()
        return self.observation, reward, done, {}

    def compute_variables_vector(self, action):
        # print('-------------------')
        # print(self.variables_vector)
        # print(f'operator: {self.operators_space[action[2]]}, scale factor: {self.scale_factors[action[1]]},'
        # f' variable_number: {action[0]}')
        if type(self.variables_vector[action[0]]) == int:
            scale_value = action[1] % len(self.scale_factors)
            # print(scale_value)
            temp = int(self.operators_space[action[2]](self.variables_vector[action[0]],
                                                       self.scale_factors[scale_value]))
            temp = max(min(temp, self.input_domain), -self.input_domain)
            self.variables_vector[action[0]] = temp
        elif type(self.variables_vector[action[0]]) == str:
            # add a begin
            if action[2] == 0:
                if len(self.variables_vector[action[0]]) < self.string_max_len:
                    self.variables_vector[action[0]] = self.alphabet[action[1]] + self.variables_vector[action[0]]
            # add at bottom
            elif action[2] == 1:
                if len(self.variables_vector[action[0]]) < self.string_max_len:
                    self.variables_vector[action[0]] = self.variables_vector[action[0]] + self.alphabet[action[1]]
            # remove at begin
            elif action[2] == 2:
                if len(self.variables_vector[action[0]]) > 0:
                    self.variables_vector[action[0]] = self.variables_vector[action[0]][1:]
            # remove at bottom
            elif action[2] == 3:
                if len(self.variables_vector[action[0]]) > 0:
                    self.variables_vector[action[0]] = self.variables_vector[action[0]][:-1]
        # print(self.variables_vector)

    def reset(self):
        self.successes = set()
        self.steps = 0
        self.variables_vector = self.template_variables_vector[:]
        self.observation = np.array([0] * self.N_OBSERVATIONS)
        return self.observation

    def compute_reward(self):
        # we reached the target
        if self.observation[self.target_line] >= 1:
            if tuple(self.variables_vector) not in self.successes:
                self.diversity_inputs.add(tuple(self.variables_vector))
                self.successes.add(tuple(self.variables_vector))
                return 1.0, self._done()
            else:
                return 0.0, self._done()
        else:
            return -1.0, self._done()

    def _done(self):
        if self.steps >= self._max_steps:
            return True
        else:
            return False

    def compute_target_line(self):
        # self.call_program()
        root = gcov.main(['-r', '.', '--xml-pretty'])
        # searching for the correct file

        for elem in root[1][0][0]:
            # the file_name is equal to the target file
            if elem.items()[1][1] == self.target_file:
                break
            self.index += 1

        counter = 0
        # offset wrt the distance computed by dist.py
        if self.config_file == 'config.ini':
            self.offset = int(root[1][0][0][self.index][1][0].items()[0][1])
            # self.offset = int(root[1][0].items()[0][1])
        else:
            self.offset = 0
        # iterating over lines
        line_in_xml_file = 0
        for code_line in root[1][0][0][self.index][1]:
            # we need to discover if it is a branch
            elements = code_line.items()
            if int(elements[0][1]) == self.branch_target_line + self.offset:
                # we have the correct line
                self.target_line = counter
                self.branches[counter] = {'line_in_code': int(elements[0][1]), 'line_in_xml_file': line_in_xml_file}
                counter += 1
            elif elements[2][1] == 'true':
                self.branches[counter] = {'line_in_code': int(elements[0][1]), 'line_in_xml_file': line_in_xml_file}
                counter += 1
            line_in_xml_file += 1
        if self.target_line == -1:
            print('no matches found: targeting branch 0')
            self.target_line = 0
        return root

    def call_compiled_program(self):
        if tuple(self.variables_vector) not in self.timeout_inputs:
            try:
                os.remove(self.file_gcda)
            except:
                pass
            # if we are using the scanf as input
            if self.scanf:
                command = b''
                for i in self.variables_vector:
                    command += bytes(str(i), 'ascii') + b' '
                try:
                    p = subprocess.run([self.exec_command], input=command, capture_output=True, timeout=1)
                except subprocess.TimeoutExpired:
                    self.timeout_inputs.add(tuple(self.variables_vector))
            # if we are not using the scanf
            else:
                command = ''
                if self.read_from_file:
                    temp = ''
                    for i in self.variables_vector:
                        temp += f' {i}\n'
                    with open('temp.txt', 'w') as f:
                        f.write(temp)
                    command = ['temp.txt']
                    command.insert(0, self.exec_command)
                else:
                    for i in self.variables_vector:
                        command += f' {i}'
                    command = sh_split(command)
                    command.insert(0, self.exec_command)
                try:
                    p = subprocess.run(command, capture_output=True, timeout=5)
                    if self.mutation_trace:
                        self.output_trace.append(p.stdout.decode())
                except subprocess.TimeoutExpired:
                    self.timeout_inputs.add(tuple(self.variables_vector))

    def call_library_program(self):
        ctypes_var = list()
        i = 0
        for actual_type in self.variables_types:
            ctypes_var.append(self.c_types[actual_type](self.variables_vector[i]))
            i += 1
        self.library_function(*ctypes_var)

    def close(self):
        pass

    def monitor_training(self):
        pass
        # self.variables_vector_history.append(list(self.variables_vector))
        # self.input_curve.append(len(self.diversity_inputs))
