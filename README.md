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

Python 3.x: The project's scripts are written in Python 3, so a compatible version is required. Download and install Python 3.x from [here](https://www.python.org/downloads/).

Bash: The main script, monitor.sh, is a Bash script. Most Unix-based systems (including Linux and macOS) come with Bash pre-installed. Windows users can use [Git Bash](https://gitforwindows.org/) or the [Windows Subsystem for Linux (WSL)](https://docs.microsoft.com/en-us/windows/wsl/).

- openpyxl: A Python library used for reading and writing Excel files. Install it using pip:
```
pip install openpyxl
```
- Illumina InterOp: A Python library for parsing Illumina run metrics. Install it using pip:
```
pip install illumina-interop
```
- Virtual environment (optional): A virtual environment allows you to manage Python dependencies for the project separately, without affecting system-wide packages. Install virtualenv using pip:
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
1. Clone the repository: Clone the project's repository to your local machine by running the following command in your terminal or command prompt:
```
git clone https://gitlab.com/gdoy/dnanexus_illumina_automator.git
```
If you don't have Git installed, you can download the repository as a ZIP file and extract it.

2. Create a virtual environment (optional): If you prefer using a virtual environment to manage the project's dependencies, navigate to the project's root directory and create a new virtual environment by running:
```
virtualenv venv
```
3. Activate the virtual environment:

On Linux and macOS:
```
source venv/bin/activate
```
On Windows:
```
venv\Scripts\activate
```
4. Install Python dependencies: Install the required Python libraries by running the following command:
```
pip install openpyxl illumina-interop
```
5. Configure settings.xml: Open the settings.xml file in a text editor and update the values for <project>, <virtual_env>, and <run_directory> according to your system and project setup.

6. Prepare input files: Ensure that the input Excel files containing sample information are formatted correctly and placed in the appropriate directory as specified in settings.xml.

7. Run the project: You can now run the main script monitor.sh from your terminal or command prompt:
```
bash monitor.sh
```
The script will start monitoring the specified run directory, generate SampleSheets, poll for RTA completion, and launch the pipeline using create_inputs.py.

## Workflow
![Image](workflow.png)

## Troubleshooting
You can refer to the monitor.log file to check console output for error messages.

## Contributors
George Doyle (developer)

## License
This project is released under the [MIT License](https://opensource.org/licenses/MIT). This license grants you permission to use, modify, and distribute the software for any purpose, including commercial use, without any restrictions or limitations. The software is provided "as is" without warranty of any kind, either express or implied, including but not limited to the warranties of merchantability, fitness for a particular purpose, and noninfringement.

By using this project, you agree to the terms of the MIT License.

## Changelog

