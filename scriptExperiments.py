######################################
## THIS FILE SHOULD NOT BE MODIFIED ##
######################################

import subprocess  # for running shell commands
from datetime import datetime  # for getting the current time
from projectUtils import *

# Create the parser
parser = argparse.ArgumentParser(description="Process command line arguments.")

# Add the arguments
parser.add_argument("-d", "--dataFolderPath", type=validFolder, required=True, help="The path to the data folder.")
parser.add_argument("-f", "--experimentsFolderPath", type=str, required=True,
					help="The path to the experiments folder.")
parser.add_argument("-m", "--models", nargs='*', type=str,choices=["MIP1", "MIP2", "Benders"], required=True,
					help="The model(s) of the problem. Must be a subset of {MIP1,MIP2,Benders}.")
parser.add_argument("-s", "--solverName", type=str, default='gurobi', choices=['gurobi', 'highs', 'cbc'],
					help="The solver name (gurobi, highs, cbc). Default is 'gurobi'.")
parser.add_argument("-t", "--timeLimit", type=positiveInt, default=600, help="The time limit. Default is 600.")
parser.add_argument("-p", "--print", action='store_true', help="Verbose output or not. Default is False.")

print("Start experiments for the parallel scheduling problem")

# Parse the arguments
args = parser.parse_args()
args.models = list(dict.fromkeys(args.models))

print("----------- ARGUMENTS -----------")
print("Data folder path:", args.dataFolderPath)
print("Experiments folder path:", args.experimentsFolderPath)
print("List of the models:", args.models)
print("Time limit:", args.timeLimit)
print("Verbose output:", args.print)
print("------------------------------------")

# Get the current time
now = datetime.now()
formatted_time = now.strftime("%Y-%m-%d_%H-%M-%S")
experimentsFolderPath = f"{args.experimentsFolderPath}_{formatted_time}"
# Create the experiments folder if it doesn't already exist
os.makedirs(experimentsFolderPath, exist_ok=True)
# Create a folder solutions and logs into the experiments folder
solutionFolderPath = os.path.join(experimentsFolderPath, "solutions")
os.makedirs(solutionFolderPath, exist_ok=True)
logFolderPath = os.path.join(experimentsFolderPath, "logs")
os.makedirs(logFolderPath, exist_ok=True)

# Write the current time to a file in the output folder
time_file = open(os.path.join(experimentsFolderPath, 'time_of_experiments.txt'), 'w')
time_file.write('Experiments were run at this time: '+str(now))
time_file.close()

failed_experiments = []

# Loop over all files in the input folder
for dataFile in os.listdir(args.dataFolderPath):
	dataFilePath = os.path.join(args.dataFolderPath, dataFile)
	dataFileName = os.path.splitext(os.path.basename(dataFile))[0]
	for model in args.models:
		print(f'Solving problem model {model} on instance {dataFileName}.')
		# Run the external command and capture the output
		cmd = ['python3', 'ParallelSchedulingSolver.py', f'-d={dataFilePath}', f'-m={model}',
				f'-f={solutionFolderPath}', f'-t={args.timeLimit}']
		if args.print:
			cmd.append('-p')
		# Print the command
		print(">", ' '.join(cmd))
		process = subprocess.run(cmd, capture_output=True, text=True)
		if process.returncode != 0:
			print(f"Error: {process.stderr}")
			failed_experiments.append((dataFileName, model))
		# Write the command output to a log file
		log_file = open(os.path.join(logFolderPath, f'{dataFileName}_{model}.log'), 'w')
		log_file.write(process.stdout)
		log_file.close()

if failed_experiments:
	with open(os.path.join(experimentsFolderPath, 'failed_experiments.txt'), 'w') as f:
		f.write("Data Model\n")
		for experiment in failed_experiments:
			f.write(f"{experiment[0]} {experiment[1]}\n")
