# Sports Tournament Scheduler
This project aims to solve instances of the single round-robin sports tournament scheduling problem. \
It uses a Docker container based on Ubuntu to run one instance or all the instances together.

## Instruction to build the Docker image
From the main project folder, change directory to the source subfolder where the Dockerfile is inserted and run: \
`docker build . -t docker-cdmo -f Dockerfile`

## Instruction to run the container
To run a single instance of the model called "name" with n teams: \
`docker run -it docker-cdmo one "name" n`

To run all the available instances together: \
`docker run -it docker-cdmo all`

To get the summary of all available models run: \
`docker run -it docker-cdmo one -h`

## Available script details
- `one_instance.py`: runs a single instance with the specified number of teams
- `all_instances.py`: runs all the instances together

## Authors
Katia Gramaccini \
Giada Triulzi
