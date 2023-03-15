# dnanexus_illumina_automator

## Description
This project consists of a set of Python and Bash scripts designed to automate the process of generating, moving, and quality checking samplesheets for Illumina-based sequencing runs. The main script, monitor.sh, is responsible for coordinating the entire process by polling for changes in the technical directory, generating samplesheets, and launching the pipeline using create_inputs.py.

Key components of the project:

- monitor.sh: The main script that manages the workflow and executes other scripts as needed.

- settings.xml: A configuration file that stores variables such as project, virtual environment path, and run directory.

- ssgen.py: A Python script that generates samplesheets from input Excel files, either for Roche combined runs or for separate TSO500 DNA and RNA runs.

- ssmove.py: A Python script that moves the generated samplesheets to the corresponding run folder based on the ExperimentName in the RunParameters.xml file. It also creates a move.txt file containing the run location.

- q_scrape.py: A Python script that checks the average Q30 and error rate of the sequencing run to ensure they meet the minimum thresholds before launching the pipeline. It creates a qc.pass file if the quality check is successful.

The project streamlines the process of generating and managing samplesheets for Illumina sequencing runs, enabling faster and more efficient execution of sequencing pipelines.

## Requirements
### Software Dependencies
To run the project, ensure that you have the following software installed:

Python 3.x: The project's scripts are written in Python 3, so a compatible version is required. Download and install Python 3.x from here.

Bash: The main script, monitor.sh, is a Bash script. Most Unix-based systems (including Linux and macOS) come with Bash pre-installed. Windows users can use Git Bash or the Windows Subsystem for Linux (WSL).

openpyxl: A Python library used for reading and writing Excel files. Install it using pip:
```
pip install openpyxl
```
Illumina InterOp: A Python library for parsing Illumina run metrics. Install it using pip:
```
pip install illumina-interop
```
Virtual environment (optional): A virtual environment allows you to manage Python dependencies for the project separately, without affecting system-wide packages. Install virtualenv using pip:
```
pip install virtualenv
```
### Hardware Requirements
The hardware requirements for this project will largely depend on the size and complexity of the input files and the number of concurrent sequencing runs being processed. However, a modern computer with a multi-core processor, sufficient RAM (at least 4GB), and ample storage space should be adequate for most use cases.

### Configuration File
The project relies on a configuration file named settings.xml that stores information about the project, virtual environment path, and run directories. Make sure this file is properly configured according to your system and project setup.

### Input Files
Ensure that the input Excel files containing sample information are formatted correctly and placed in the appropriate directory as specified in settings.xml.

## Installation
Within a particular ecosystem, there may be a common way of installing things, such as using Yarn, NuGet, or Homebrew. However, consider the possibility that whoever is reading your README is a novice and would like more guidance. Listing specific steps helps remove ambiguity and gets people to using your project as quickly as possible. If it only runs in a specific context like a particular programming language version or operating system or has dependencies that have to be installed manually, also add a Requirements subsection.

## Usage
Use examples liberally, and show the expected output if you can. It's helpful to have inline the smallest example of usage that you can demonstrate, while providing links to more sophisticated examples if they are too long to reasonably include in the README.

## Workflow
Tell people where they can go to for help. It can be any combination of an issue tracker, a chat room, an email address, etc.

## Troubleshooting
If you have ideas for releases in the future, it is a good idea to list them in the README.

## Contributors
George Doyle (developer)

## License


## Changelog

