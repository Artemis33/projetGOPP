import os

class ParallelSchedulingData:
	"""
	A class used to represent the Parallel Scheduling Data

	Attributes
	----------
	_name : str 
		a string that holds the name of the instance to solve
		_nbJob = 0         Number n of jobs
		_nbMachine = 0     Number m of machines
		_nbFamille = 0     Number b of families of the jobs
		_familles = []     list of families of jobs
		_durees = []       matrix of [p_kj pour tout k] pour tout j
		_setups = []       matrix of [[s_kff' pour tout f] pour tout f'] pour tout k
	Methods
	-------
	__init__(self, fileName)
		Initializes the ParallelSchedulingData with the provided file named fileName.
	readData(self, fileName)
		Reads the data in the provided file with the name fileName
	__str__(self)
		Displays the data
	doOrdre(preds)
		Do the vector of positions provided with a list of precedences preds

	"""
	def __init__(self, fileName):
		self._name = os.path.splitext(os.path.basename(fileName))[0]
		self._nbJob = 0        # Nombre n de jobs
		self._nbMachine = 0    # Nombre m de machines
		self._nbFamille = 0    # Nombre b de familles de tâches
		self._familles = []    # liste des familles des jobs
		self._durees = []      # matrice avec [p_kj pour tout k] pour tout j
		self._setups = []      # matrice avec [[s_kff' pour tout f] pour tout f'] pour tout k
		self.readData(fileName)


	def readData(self,fileName):
		try:
			with open(fileName, 'r') as file:
				# Premiere ligne : nombre de tâches
				line = file.readline().strip()
				self._nbJob = int(line)

				# Deuxieme ligne : nombre de machines
				line = file.readline().strip()
				self._nbMachine = int(line)

				#Troisieme ligne : nombre de familles de tâches
				line = file.readline().strip()
				self._nbFamille = int(line)
				n = self._nbJob
				m = self._nbMachine
				b = self._nbFamille
				# On va lire les temps d'exécution des tâches sur chaque machine 
				for j in range(n):
					line = file.readline().strip().split()
					job = []
					self._familles.append(int(line[0]) - 1)
					for k in range(1,len(line)):
						job.append(int(line[k]))
					self._durees.append(job)
				for k in range(m):
					machine = []
					for f in range(b):
						line = file.readline().strip().split()
						setup = []
						for g in range(b):
							setup.append(int(line[g]))
						machine.append(setup)
					self._setups.append(machine)
		except Exception as e:
			print(f"An error occurred while reading the file: {e}")

	def __str__(self):
		return (f"Number of jobs: {self._nbJob}\t"
				f"Number of machines: {self._nbMachine}\t"
				f"Number of families: {self._nbFamille}\n"
				f"Families: {self._familles}\n"
				f"Processing times: {self._durees}\n"
				f"setups: {self._setups}")

def doOrdre(preds):
	taille = len(preds) + 1
	ordre = [-1 for i in range(taille)]
	# On cherche la première tâche sur la machine avec la liste des arcs
	first = preds[0][0]
	for [i,j] in preds:
		for [i,j] in preds:
			if (j == first):
				first = i
	pred = first
	ordre[0] = pred
	# On établit à la suite l'ordre de passage des âches sur la machinbe à partir de la liste des précédences
	for k in range(1,taille):
		for [i,j] in preds:
			if (i==pred):
				ordre[k] = j
				pred = j
				break
	
	return ordre
