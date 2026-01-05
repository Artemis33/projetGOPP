from ParallelSchedulingData import *

class ParallelSchedulingSolution:
	"""
	A class used to represent the Parallel Scheduling Solution

	Attributes
	----------
	_name : str
		a string that holds the name of the instance solved
	_value : int 
		an integer that holds the value of the solution
	_compoMachine : matrix
		a matrix with the composition of each machine

	Methods
	-------
	__init__(self, name)
		Initializes the ParallelSchedulingSolution with the provided name.
	saveSolution(self, fileName)
		Saves the solution in the provided file with the name fileName
	readSolution(self, fileName)
		Reads a solution in the provided file with the name fileName
	__str__(self)
		Displays the solution
	checkSolution
		Check if the solution if feasible

	"""
	def __init__(self, name):
		self._name = name
		self._value = 0         # Cmax
		self._compoMachine = [] # matrice avec les ordonnancements des jobs sur chaque machine

	def saveSolution(self, fileName):
		if self is None:
			print("Solution vide")
			return None
		m = len(self._compoMachine)
		with open(fileName, 'w') as file:
			file.write(self._name + "\n")
			file.write(str(int(self._value)) + "\n")
			for k in range(m):
				machine = self._compoMachine[k]
				for j in machine:
					file.write(str(j+1) + " ")
				file.write("\n")


	def readSolution(self, fileName):
		try:
			with open(fileName, 'r') as file:
				line = file.readline().strip()
				self._name = line
				line = file.readline()
				self._value = int(line)
				while(line!=""):
					line = file.readline()
					if line:
						machine = line.strip().split()
						self._compoMachine.append(machine)

		except Exception as e:
			print(f"An error occurred while reading the file: {e}")

	def __str__(self):
		csv, colsep, rowsep = '', ', ', '\n' # set col and row separators
		csv += f"Nom de l'instance: {self._name}\t" + f"Makespan: {self._value}\n" 
		cpt2=0
		for machine in self._compoMachine:
			cpt=0
			cpt2 += 1
			for j in machine:
				colsep = ', '
				cpt += 1
				if (cpt==len(machine)):
					colsep = ''
				csv += f"{j}{colsep}" # append value and separator to CSV string
			if (cpt2==len(self._compoMachine)):
				rowsep = ''
			csv += f"{rowsep}"		
		return (csv)

	def checkSolution(self, data:ParallelSchedulingData):
		# Ck <= Cmax check
		Cmax = self._value # valeur de la solution
		C = []             # vecteur des dates de fin des machines
		for k in range(data._nbMachine):
			duree = 0
			# print(len(self._compoMachine[k]) - 1)
			for j in self._compoMachine[k]:                   # Ajout des durées des tâches de la machine k pour Ck
				duree += data._durees[j][k]
			for cpt in range(len(self._compoMachine[k]) - 1): # Ajout des temps de setups sur k
				jk   = self._compoMachine[k][cpt]
				jkp1 = self._compoMachine[k][cpt+1]
				f_jk = data._familles[jk]
				f_jkp1 = data._familles[jkp1]
				duree += data._setups[k][f_jk][f_jkp1]
			C.append(duree)
		CmaxCalc = max(C)
		# print(C)
		if (Cmax != CmaxCalc):
			return False
		return True