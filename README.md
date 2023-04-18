# dnanexus_illumina_automator

## Description
This repository contains a collection of Python scripts designed to automate the processing of DNA sequencing data. The pipeline polls a technical directory for changes, generates SampleSheets, checks for completion of Real-Time Analysis (RTA), and launches a pipeline via a Python script. It interacts with a SQLite database to track the progress of each run folder through the pipeline and scrapes the DNAnexus API to monitor the status of demultiplexing and analysis.

![Image](dashboard.png)

## Features
- Monitor a technical directory for changes
- Generate and move SampleSheets to the corresponding run folders
- Check for completion of Real-Time Analysis (RTA)
- Launch a pipeline via a Python script
- Track the progress of each run folder through a SQLite database
- Scrape the DNAnexus API to monitor the status of demultiplexing and analysis
- Check if Q30 and error rate exceed a minimum threshold before launching the pipeline
- Generate Q-score histogram plot and scatter plot
- Serve a dashboard displaying run status and metrics using Flask

## Requirements
- Python 3.x
- Docker (for Docker deployment)
- Libraries: Flask, SQLite, xml, csv, DNAnexus, and other dependencies

## Installation
1. Clone the repository: Clone the project's repository to your local machine by running the following command in your terminal or command prompt:
```
git clone https://gitlab.com/gdoy/dnanexus_illumina_automator.git
```
If you don't have Git installed, you can download the repository as a ZIP file and extract it.

2. Install the required libraries.
```
pip install -r requirements.txt
```

# Docker Deployment

1. Build the Docker image by running the following command from the root of your project directory:
```
docker build -t nexus_automator .
```

2. Run a Docker container based on your newly created image:
```
docker run -p 5000:5000 nexus-automator
```

3. Access the dashboard by navigating to http://localhost:5000 in your web browser.

## Usage

1. Configure the main.py main() function with the appropriate directories and database information.
2. Run monitor.py to start the pipeline monitoring process.

## Scripts Description

- monitor.py: Monitors a technical directory for changes, generates SampleSheets, checks for completion of RTA, and launches a pipeline via a Python script.
- q_scrape.py: Checks if Q30 and error rate exceed a minimum threshold before launching the pipeline, extracts data from InterOp files, parses XML files, updates the SQLite database, and generates plots.
- ssgen.py: Moves samplesheets to their corresponding run folder based on RunParameters.xml and generates correctly formatted samplesheets.
- ssmove.py: Moves csv files to the output directory based on a search string that matches the ExperimentName in RunParameters.xml.
- dashboard.py: Defines a Flask web application that serves a dashboard page displaying run status and metrics retrieved from the SQLite database.

## Workflow
![Image](workflow.png)

## Troubleshooting
You can refer to the monitor.log file to check console output for error messages.

## Contributors
George Doyle (developer)

## License
The software is provided "as is" without warranty of any kind, either express or implied, including but not limited to the warranties of merchantability, fitness for a particular purpose, and noninfringement.

By using this project, you agree to the terms of the [MIT License](https://opensource.org/licenses/MIT).

## Changelog
1.01 (28/03/2023) - Script now dependent on SQLite checks. Flask dashboard added. DNAnexus polling for demultiplex completion.