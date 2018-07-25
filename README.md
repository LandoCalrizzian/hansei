Test automation framework for project-koku

[project-koku] <https://github.com/project-koku>
- [koku] <https://github.com/project-koku/koku>
- [koku-ui] <https://github.com/project-koku/koku-ui>
- [masu] <https://github.com/project-koku/masu>

# Getting Started
This is a Python project developed using Python 3.6. Make sure you have at least this version installed.

# Development
To get started developing against Hansei first clone a local copy of the git repository.
`git clone https://github.com/project-koku/hansei`

Developing inside a virtual environment is recommended. A Pipfile is provided. Pipenv is recommended for combining virtual environment (virtualenv) and dependency management (pip).
To install pipenv to ~/.local/bin, use
`pip3 install --user pipenv`

Then project dependencies and a virtual environment can be created using
`pipenv install --dev`

To activate the virtual environment run
`pipenv shell`

To run a single command inside a virtual environment
`pipenv run <CMD>

# Configuration
This project is developed using the pytest test automation framework. Many configuration settings can be read in from a config.yaml file.
An example file example_config.yaml is provided in the repository. To use the defaults simply

`cp example_config.yaml config.yaml`

config.yaml can also be stored in ~/.config/hansei/ if there is no config.yaml in the hansei repo root directory

# Running smoke tests
Currently all tests are located in hansei/tests/ with api and ui tests separated into separate subfolders

Smoke tests can be run by specifying the smoke test marker during pytest execution
`pipenv run pytest -v -m smoke`
