from ParallelSchedulingData import *
from ParallelSchedulingSolution import *
import math
import pyomo.environ as pe 
import pyomo.opt as po
from pyomo.core import quicksum

class ParallelSchedulingMIP1:
	def __init__(self):
		"""
		Initialize the scheduler with the model to solve the Parallel Scheduling Problem.
		"""
		self._model = None

	def runMIP1(self, data:ParallelSchedulingData, solverName, timeLimit, verbose=False):
		"""
		Solves the MIP1 self._model for the problem.

		Parameters
		----------
		data : data(ParallelSchedulingData)
			the data to be used for the problem
		solverName : str
			the name of the solver to be used
		timeLimit :
			the time limit for the solver
		verbose : bool, optional
			a flag used to control the verbosity of the function (default is False)

		Returns
		-------
		ParallelSchedulingSolution
			an object of class ParallelSchedulingSolution representing the solution
		"""
		# On met les données avec les notations du problème
		n = data._nbJob
		m = data._nbMachine
		b = data._nbFamille
		bigM = n

		# On récupère les données individuelles 
		f = data._familles
		durees   = data._durees
		setups   = data._setups

		# Création du modèle vide
		self._model = pe.ConcreteModel(name="MIP1")
		
		# Création des variables
		self._model.x    =    pe.Var(range(n), range(n), range(m), name="x", bounds=(0,1), domain=pe.Binary) # x_ijk
		self._model.y    =    pe.Var(range(n), range(m), name='y', bounds=(0,1), domain=pe.Binary)           # y_jk
		self._model.C    =    pe.Var(range(m), name='C', domain=pe.NonNegativeReals)                         # C_k
		self._model.Cmax =    pe.Var(name='Cmax', domain=pe.NonNegativeReals)                                # C_max
		self._model.u    =    pe.Var(range(n), range(m), name='u', domain=pe.NonNegativeReals)               # u_jk
		
		# Ajout de la fonction objectif au modèle
		self._model.obj = pe.Objective(expr = self._model.Cmax, sense = pe.minimize)
		
		# Ajout des contraintes au modèle
		self._model.contraintes1    = pe.ConstraintList() # Cmax >= Ck pour tout k
		self._model.contraintes2    = pe.ConstraintList() # Ck >= durees des taches lui etant affectees + temps de setup
		self._model.contraintes4    = pe.ConstraintList() # Si la tâche i est affectée à la machine k elle au moins 1 précédence et/ou 1 successeur
		self._model.contraintes5    = pe.ConstraintList() # Chaque tâche ne peut être affectée qu'à une seule machine
		self._model.contraintes7    = pe.ConstraintList() # Chaque tâche a au plus un predecesseur 
		self._model.contraintes8    = pe.ConstraintList() # Chaque tâche a au plus un successeur 
		self._model.contraintesX    = pe.ConstraintList() # Les variables x_jjk sont à 0 car aucun sens de les affecter
		self._model.contraintesMTZ  = pe.ConstraintList() # Contraintes de sous-tour pour casser les cycles pour la solution
		self._model.contraintesPos  = pe.ConstraintList() # Contraintes avec MTZ pour limiter les positions
		self._model.contraintesSym  = pe.ConstraintList() # Contraintes pour limiter les symétries
		for k in range(m):
			self._model.contraintes1.add(self._model.Cmax >= self._model.C[k])
			self._model.contraintes2.add( self._model.C[k] >= quicksum(durees[j][k] * self._model.y[j,k] for j in range(n)) + quicksum(setups[k][f[i]][f[j]] * self._model.x[i,j,k] for j in range (n) for i in range(n)) )
			self._model.contraintes4.add(quicksum(self._model.x[i,j,k] for i in range(n) for j in range(n)) >= quicksum(self._model.y[i,k] for i in range(n)) - 1)
			for j in range(n):
				self._model.contraintesX.add(self._model.x[j,j,k]==0)
				self._model.contraintes7.add(quicksum(self._model.x[i,j,k] for i in range(n)) <= self._model.y[j,k])
				self._model.contraintes8.add(quicksum(self._model.x[j,i,k] for i in range(n)) <= self._model.y[j,k])
				self._model.contraintesPos.add(self._model.u[j,k] <= bigM *  self._model.y[j,k])
				for i in range(n):
					self._model.contraintesMTZ.add(self._model.u[j,k] >= self._model.u[i,k] + 1 - bigM * (1 - self._model.x[i,j,k]))

		for i in range(n):
			self._model.contraintes5.add(quicksum(self._model.y[i,k] for k in range(m)) == 1)
			for j in range(i):
				if (f[i] == f[j]):
						self._model.contraintesSym.add(quicksum(self._model.x[i,j,k] for k in range(m))==0)

		
		#Résolution du modele
		solver_name = solverName
		if po.SolverFactory(solver_name).available():
			print("Solver " + solver_name + " is available.")
		else:
			print("Solver " + solver_name + " is not available.")
		solver = po.SolverFactory(solver_name)
		if solver_name == 'appsi_highs':
			solver.options['time_limit'] = timeLimit
			solver.options['mip_rel_gap'] = 1e-6
			solver.options['mip_abs_gap'] = 0.99
		elif solver_name == 'cbc':
			solver.options['seconds'] = timeLimit
			solver.options['ratioGap'] = 1e-4
			solver.options['allowableGap'] = 0.99
		elif solver_name == 'gurobi':
			solver = po.SolverFactory(solver_name, solver_io="python")
			solver.options["TimeLimit"] = timeLimit
			solver.options["MIPGap"] = 1e-4
			solver.options["MIPGapAbs"] = 0.99
		results = solver.solve(self._model,tee=False)
		print("\n----------------------------------")
		print("Temps de résolution (s) : ", results.solver.wallclock_time)
		print("Status du solveur = ", results.solver.status)
		print("Status de la résolution = ", results.solver.termination_condition)
		print("Borne Inférieure: ", results.problem.lower_bound)
		print("Borne Supérieure: ", results.problem.upper_bound)
		UB = results.problem.upper_bound
		LB = results.problem.lower_bound
		if (UB != 0):
			Gap = ((UB - LB)/abs(UB))*100  # Gap
		elif (UB == 0) and (LB == 0):
			Gap = 0
		print("Gap: ", Gap)
		print("----------------------------------")
		# Si le modèle a été résolu à l'optimalité ou si une solution a été trouvée dans le temps limite accordé
		if results.solver.termination_condition==po.TerminationCondition.optimal or results.solver.termination_condition==po.TerminationCondition.maxTimeLimit:
			# Si une solution a été trouvée (optimale ou meilleure solution calculée dans le temps limite accordé)
			print("Solution calculée")
			print("Valeur de la solution =", pe.value(self._model.obj))
			print("----------------------------------")
			# for k in range(m):
			# 	for j in range(n):
			# 		if (pe.value(self._model.y[j,k]) > 0.5):
			# 			print("machine ", k+1, " job ", j+1, "\n")
			# 		for i in range(n):
			# 			if (pe.value(self._model.x[i,j,k]) > 0.5):
			# 				print(i+1, " est avant ", j+1, " sur la machine k ", k+1, "\n")

			solution=ParallelSchedulingSolution(data._name)
			solution._value=pe.value(self._model.obj)
			for k in range(m):
				machine = []
				preds = []
				for i in range(n):
					for j in range(n):
						if (pe.value(self._model.x[i,j,k]) > 0.5):
							preds.append([i,j])
				machine = doOrdre(preds)
				solution._compoMachine.append(machine)	
			return solution
		

def doOrdre(preds): # Récupération de l'ordre des tâches à partir des précédences
	taille = len(preds) + 1
	ordre = [-1 for i in range(taille)]
	first = preds[0][0]
	for [i,j] in preds:
		for [i,j] in preds:
			if (j == first):
				first = i
	pred = first
	ordre[0] = pred
	for k in range(1,taille):
		for [i,j] in preds:
			if (i==pred):
				ordre[k] = j
				pred = j
				break
	
	return ordre


