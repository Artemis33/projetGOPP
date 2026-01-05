from ParallelSchedulingMIP1 import *
from ParallelSchedulingMIP2 import *
import time
from projectUtils import *
import sys

# Create the command line parser
parser = argparse.ArgumentParser(description="Process command line arguments.")

# Add the arguments
parser.add_argument("-d", "--dataFilePath", type=validFile, required=True, help="The path to the data file.")
parser.add_argument("-m", "--model", type=str, required=True, choices=["MIP1", "MIP2"], help="The model to solve the problem.")
parser.add_argument("-s", "--solverName", type=str, default='gurobi', choices=['gurobi', 'highs', 'cbc'], help="The solver name (gurobi, highs, cbc). Default is 'gurobi'.")
parser.add_argument("-t", "--timeLimit", type=positiveInt, default=600, help="The time limit. Default is 600.")
parser.add_argument("-p", "--print", action='store_true', help="Verbose output or not. Default is False.")
parser.add_argument("-f", "--solutionFolderPath", type=validFolder, required=True, help="The path to the solution folder.")

# Parse the arguments
args = parser.parse_args()
print("----------- ARGUMENTS -----------")
print("Data file path =", args.dataFilePath)
print("Problem model =", args.model)
print("Solver name =", args.solverName)
print("Time limit =", args.timeLimit)
print("Verbose output =", args.print)
print("Solution folder path =", args.solutionFolderPath)
print("------------------------------------")

if args.solverName == 'highs':
    args.solverName = 'appsi_highs'


# Check if the solver is available
if po.SolverFactory(args.solverName).available():
    print("Solver " + args.solverName + " is available.")
else:
    print("Solver " + args.solverName + " is not available.")
    sys.exit(0)

# Read the data from the file
dataFileName = os.path.splitext(os.path.basename(args.dataFilePath))[0]
print(args.dataFilePath)
data = ParallelSchedulingData(args.dataFilePath)
# print(data)

# Solve the problem
begin = time.time()
if args.model == "MIP1":
	if args.print:
		print("Considering model 1 of the problem")
	inst = ParallelSchedulingMIP1()
	solution = inst.runMIP1(data, args.solverName, args.timeLimit, args.print)

elif args.model == "MIP2":
	if args.print:
		print("Considering model 2 of the problem")
	inst = ParallelSchedulingMIP2()
	solution = inst.runMIP2(data, args.solverName, args.timeLimit, args.print)

# elif args.model == "Benders":
# 	if args.print:
# 		print("Considering Benders model of the problem")
# 	inst = ParallelSchedulingBenders()
# 	solution = inst.runMILPBenders(data, args.solverName, args.timeLimit, args.print)

else:
	print("Unknown model of the problem")
	sys.exit(0)
end = time.time()


# Check the solution
isFeasible = solution.checkSolution(data)
print(isFeasible)
if (isFeasible):
	print("check valide")


# Save the solution
if (solution!=False):
	solutionFilePath = dataFileName + "_" + str(args.model) + ".txt"
	if args.solutionFolderPath != "":
		solutionFilePath = os.path.join(args.solutionFolderPath, solutionFilePath)
	print("Solution is written in the following file: ", solutionFilePath)
	solution.saveSolution(solutionFilePath)

# Print the result and exit
print("\nInstance =", dataFileName)
print("Modèle =", args.model)
if (solution!=False):print("Valeur de la solution =", round(solution._value))
print("cpuTime =", float(end - begin))
sys.exit(0)
