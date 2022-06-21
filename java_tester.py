import configparser
import json
import operator
import os
import sys
from os.path import exists
from xml.dom import minidom

import gym
import numpy as np
import requests


def to_string(tree):
    temp = ''
    for code_line in tree[1][0][0][0][1]:
        temp += str(code_line.items())
    return temp


class java_tester(gym.Env):

    def __init__(self, config_file, input_boundary=True, input_domain=6000,
                 episode_length=15_000):
        super(java_tester, self).__init__()
        self.ops = {
            '+': operator.add,
            '-': operator.sub,
            '*': operator.mul,
            '/': operator.truediv,
            '%': operator.mod,
            '^': operator.xor
        }

        self.index = 0
        self.config_file = os.path.basename(config_file)
        self.alphabet = 'abcdefghijklmnopqrstuvwxyz ;(){}[]1234567890?:.+-*/&|%"~'
        # in case a certain input breaks the program
        self.timeout_inputs = set()

        self.input_boundary = input_boundary
        # these are used when you want to collect the output coming from the program execution
        self.output_trace = list()

        # saving all inputs in an episode
        self.successes = set()
        # collects all input generated during training
        self.variables_vector_history = list()

        self.config = configparser.ConfigParser()
        self.config.read(config_file)

        self.jacococli_jar = self.config['DEFAULT']['jacococli_jar']
        self.result_jacoco_exec = self.config['DEFAULT']['result_jacoco_exec']
        self.result_jacoco_xml = self.config['DEFAULT']['result_jacoco_xml']
        self.source_files = self.config['DEFAULT']['source_files']
        self.class_files = self.config['DEFAULT']['class_files']
        self.endpoint = json.loads(self.config['DEFAULT']['endpoint'])
        self.url = self.config['DEFAULT']['url']
        self.file_create_with_command = os.path.dirname(__file__) + "/test_command_injection"
        if os.path.exists(self.file_create_with_command):
            os.remove(self.file_create_with_command)
        self.cmd_to_inject = "touch " + self.file_create_with_command

        # Mettere quanti valori prende in ingresso l'endpoint
        parameters_ = self.endpoint['restEndpoint']['parameters']
        name_cmd_var = self.endpoint['nameCmdVar']
        type_cmd_var = self.endpoint['typeCmdVar']

        for index, param in enumerate(parameters_):
            if param["name"] == name_cmd_var and param["format"].upper() == type_cmd_var.upper():
                self.cmd_param_index = index

        self.variables_space = len(parameters_)
        # these are used when you want to compute diversity
        self.input_domain = input_domain

        self.string_max_len = 5

        self.strings_use = False if self.config['DEFAULT']['strings_use'] == 'False' else True

        # TODO da completare se tipo diverso da number/str
        self.variables_types = []
        for parameter in parameters_:
            self.variables_types.append('int' if parameter['format'] == 'number' else 'str')

        # initializing the variable vector
        self.variables_vector = list()
        for elem_type in self.variables_types:
            value = 0 if (elem_type == 'int') else ''
            self.variables_vector.append(value)

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

        # name of the end_point
        self.target_file = self.config['DEFAULT']['target_file']

        self.observation = np.array([])
        # launching the program for the first time to determine the observation space

        self.step([0, 0, 0])

        self.N_OBSERVATIONS = len(self.observation)
        if self.strings_use:
            self.action_space = gym.spaces.MultiDiscrete([self.variables_space, len(self.alphabet),
                                                          len(self.operators_space)])
        else:
            self.action_space = gym.spaces.MultiDiscrete([self.variables_space, len(self.scale_factors),
                                                          len(self.operators_space)])

        self.observation_space = gym.spaces.Box(low=-input_domain, high=input_domain,
                                                shape=(self.N_OBSERVATIONS,))

    @staticmethod
    def check_node(jacoco_result, node):
        file_path = node["file"].split("/")
        name_file = file_path.pop()
        line_file = node["line"]

        my_file = None
        for elem in jacoco_result.getElementsByTagName('sourcefile'):
            if elem.attributes['name'].value == name_file:
                my_file = elem
                break

        if my_file is None:
            raise Exception("file not found")

        my_line = None
        for line in my_file.getElementsByTagName('line'):
            if line.attributes['nr'].value == str(line_file):
                my_line = line
                break

        if my_line is None:
            return "-1"

        print('Check node:', my_file.attributes['name'].value, ' - ', my_line.attributes['nr'].value)

        return my_line.attributes['ci'].value

    def get_observation(self):
        jacoco_result = minidom.parse(self.result_jacoco_xml)
        steps = self.endpoint["steps"]

        observation = np.array([])
        for step in steps:
            single_observation = self.check_node(jacoco_result, step)
            observation = np.append(observation, [single_observation])

        for element in self.variables_vector:
            if element != self.cmd_to_inject and type(element) == str:
                pos = ''
                for letter in element:
                    pos += str(self.alphabet.find(str(letter)))
                pos = 0 if pos == '' else pos
                observation = np.append(observation, int(pos))
            else:
                observation = np.append(observation, element)
        return observation

    def exec_request(self):
        rest_endoint = self.endpoint["restEndpoint"]
        url = self.url
        path = '/'.join([rest_endoint["rootPath"], rest_endoint["path"]])
        method = rest_endoint["method"]
        params = rest_endoint["parameters"]

        endpoint = url + path
        if method == "GET":
            query_param = []
            for index, param in enumerate(params):
                value = self.variables_vector[index]
                if param["typeParameter"] == "QUERY_PARAM":
                    query_param.append(param["name"] + "=" + value)
                elif param["typeParameter"] == "PATH_PARAM":
                    endpoint = endpoint.replace("{" + param["name"] + "}", value)

            if len(query_param) > 0:
                query_param = "?" + '&'.join(query_param)
            else:
                query_param = ""

            endpoint = endpoint + query_param
            print("execute request: ", endpoint)
            r = requests.get(endpoint)
            print("this is the status_code result: ", r.status_code)
            return
        else:  # TODO implementare logica per POST e PUT
            print("method", method, "is not supported")
            sys.exit()

    def dump_jacoco_result(self):
        cmd = ["java", "-jar", self.jacococli_jar, "dump --destfile", self.result_jacoco_exec, "--reset"]
        os.system(' '.join(cmd))

    def generate_jacoco_xml_result(self):
        cmd = ["java", "-jar", self.jacococli_jar, "report", self.result_jacoco_exec, "--xml", self.result_jacoco_xml,
               "--sourcefiles", self.source_files, "--classfiles", self.class_files]
        os.system(' '.join(cmd))

    def delete_jacoco_result(self):
        if os.path.exists(self.result_jacoco_exec):
            os.remove(self.result_jacoco_exec)

    def check_and_write_result(self):
        file_exists = exists(self.file_create_with_command)

        lines = ["command line executed with variable: " + str(self.variables_vector)]
        if file_exists:
            lines.append("the injected command was executed")
        with open('result/result.txt', 'w') as f:
            for line in lines:
                f.write(line)
                f.write('\n')

    def step(self, action):
        self.compute_variables_vector(action)

        # exec request
        self.exec_request()

        # get result jacoco
        self.delete_jacoco_result()
        self.dump_jacoco_result()
        self.generate_jacoco_xml_result()

        # computing the observation
        old_observation = self.observation.copy()
        self.observation = self.get_observation()
        reward, done = self.compute_reward(old_observation)
        if reward >= 1.0:
            print("command line executed with variable:", self.variables_vector)
            self.check_and_write_result()
            sys.exit()
        self.steps += 1
        # self.monitor_training()
        return self.observation, reward, done, {}

    def compute_variables_vector(self, action):
        # print('-------------------')
        # print(self.variables_vector)
        # print(f'operator: {self.operators_space[action[2]]}, scale factor: {self.scale_factors[action[1]]},'
        # f' variable_number: {action[0]}')
        index_var_vector = action[0]
        if index_var_vector == self.cmd_param_index:  # TODO implementare la logica per cambiare comando in base al risultato
            self.variables_vector[index_var_vector] = self.cmd_to_inject
        elif type(self.variables_vector[index_var_vector]) == int:
            scale_value = action[1] % len(self.scale_factors)
            # print(scale_value)
            temp = int(self.operators_space[action[2]](self.variables_vector[index_var_vector],
                                                       self.scale_factors[scale_value]))
            temp = max(min(temp, self.input_domain), -self.input_domain)
            self.variables_vector[index_var_vector] = temp
        elif type(self.variables_vector[index_var_vector]) == str:
            # add a begin
            if action[2] == 0:
                if len(self.variables_vector[index_var_vector]) < self.string_max_len:
                    self.variables_vector[index_var_vector] = self.alphabet[action[1]] + self.variables_vector[
                        index_var_vector]
            # add at bottom
            elif action[2] == 1:
                if len(self.variables_vector[index_var_vector]) < self.string_max_len:
                    self.variables_vector[index_var_vector] = self.variables_vector[index_var_vector] + self.alphabet[
                        action[1]]
            # remove at begin
            elif action[2] == 2:
                if len(self.variables_vector[index_var_vector]) > 0:
                    self.variables_vector[index_var_vector] = self.variables_vector[index_var_vector][1:]
            # remove at bottom
            elif action[2] == 3:
                if len(self.variables_vector[index_var_vector]) > 0:
                    self.variables_vector[index_var_vector] = self.variables_vector[index_var_vector][:-1]
        # print(self.variables_vector)

    def reset(self):
        self.successes = set()
        self.steps = 0
        self.variables_vector = self.template_variables_vector[:]
        self.observation = np.array([0] * self.N_OBSERVATIONS)
        return self.observation

    def step_forward_done(self, old_observation):
        n_steps = len(self.endpoint["steps"])
        old_observation_step = 0
        if len(old_observation) > 0:
            for x in range(n_steps):
                if int(old_observation[x]) > 0:
                    old_observation_step = x
                else:
                    break

        new_observation_step = 0
        for x in range(n_steps):
            if int(self.observation[x]) > 0:
                new_observation_step = x
            else:
                break

        return new_observation_step >= old_observation_step

    def compute_reward(self, old_observation):
        # sono arrivato in fondo?
        n_steps = len(self.endpoint["steps"])

        # we reached the target
        if int(self.observation[n_steps - 1]) >= 1:
            return 1.0, self._done()
        elif self.step_forward_done(old_observation):
            return 0.0, self._done()
        else:
            return -1.0, self._done()

    def _done(self):
        if self.steps >= self._max_steps:
            return True
        else:
            return False

    def close(self):
        pass

    def monitor_training(self):
        pass
        # self.variables_vector_history.append(list(self.variables_vector))
        # self.input_curve.append(len(self.diversity_inputs))
