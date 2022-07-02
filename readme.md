# JIFRIT

## Requirements

- python3
- MacOS or Ubuntu

## Installation & Setup

- Create a virtualenv `venv` in IFRIT folder: `virtualenv -p python3 venv` and source it `source venv/bin/activate`
- Install the requirements `requirements.txt` using the command `pip3 install -r requirements.txt` 


## Using JIFRIT

- Export PYTHONPATH: `export PYTHONPATH="path/to/IFRIT"`
- Generate the main folder containing each c program's folders and put them inside (look at `programs` folder).
- Activate the venv
- create `config.ini` file from `confic.example.ini` file

## Launching JIFRIT

Once started, JIFRIT testes all ranning Java REST program   
JIFRIT uses several flags:
- ``--train_type``; 0=standard tests, 1=mutation tests
- ``--timesteps``; maximum train duration
- ``--input_domain``; numeric input domain
- ``--episode_lenght``; the episode length
- ``--sast_result``; json of model
- ``--jacococli_jar``; path of `jacococli.jar`
- ``--source_files``; directory of source code
- ``--class_files``; directory of compiled class
- ``--url``; url to application

e.g.:

```shell
python3 main.py --timesteps 2000000 --input_domain 6000 --episode_length 6000 --timer 60 \
--sast_result ./test/sast_result.json \
--jacococli_jar ./jacoco/jacococli.jar \
--source_files ./codeql_source/src/main/java \
--class_files ./codeql_source/target/classes \
--url http://localhost:8080
```

## Running the standard tests



## Running the mutation tests

Set a folder containing the c programs to be tested. The folder must contain the following files: 
The original program, the mutated programs. All the programs will be sorded, and the original program will be the first one of the list.


## Special programs

Usually, IFRIT can automatically infer the target function and the number of parameters requested as input.
Sometimes, the c program under test may be composed of several c files and several folders.
In this case, you need to define a custom config file that must be named `config_manual.ini`. It contains the required info to compile and use the program
In folder `programs/printtokens`, you can find the example file `config_manual.ini` 
