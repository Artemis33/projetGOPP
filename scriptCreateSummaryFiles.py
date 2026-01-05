######################################
## THIS FILE SHOULD NOT BE MODIFIED ##
######################################

from projectUtils import *

# Create the parser
parser = argparse.ArgumentParser(description="Process command line arguments.")

# Add the arguments
parser.add_argument("-l", "--logFolderPath", type=validFolder, required=True, help="The path to the log folder.")

# Parse the arguments
args = parser.parse_args()
print("----------- ARGUMENTS -----------")
print("Log folder path:", args.logFolderPath)
print("------------------------------------")

# Define the list of keys to search for
keys = ['Instance', 'Modèle', 'Borne Inférieure', 'Borne Supérieure', 'Gap', 'Valeur de la solution', 'cpuTime']

# Combine all log files into a single CSV summary
summaryFilePath = os.path.join(args.logFolderPath,'result_summary.csv')
summaryFile = open(summaryFilePath, 'w')
for logFile in os.listdir(args.logFolderPath):
    if logFile.endswith('.log'):
        log_path = os.path.join(args.logFolderPath, logFile)
        values = {key: "missing" for key in keys}
        with open(log_path, 'r') as f:
            for line in f:
                for key in keys:
                    if key + ' =' in line:
                        _, value = line.strip().split(' =')
                        values[key] = value
                        break
                    if key + ':' in line:
                        _, value = line.strip().split(':')
                        values[key] = value
                        break
        summaryFile.write(f'{";".join(values.values())}\n')
summaryFile.close()

# Check if the file is empty and remove it if it is
if os.stat(summaryFilePath).st_size == 0:
    os.remove(summaryFilePath)
    print("No summary file created because no log files were found")
else:
    print("Summary of the experiments written in the following file:", summaryFilePath)
