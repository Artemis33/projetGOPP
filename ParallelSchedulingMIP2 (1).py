from ParallelSchedulingData import *
from ParallelSchedulingSolution import *
import math
import pyomo.environ as pe 
import pyomo.opt as po
from pyomo.core import quicksum

class ParallelSchedulingMIP2:
	"""
	Modèle M2 : formulation à temps discret (time-indexed) du problème
	à partir d'un objet ParallelSchedulingData.
	"""

	def __init__(self):
		self.model = None

	def runMIP2(self, data:ParallelSchedulingData, solverName, timeLimit, verbose=False):
		"""
		Solves the MIP2 self._model for the problem.

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
		bigM = b

		# On récupère les données individuelles 
		familles = data._familles
		durees   = data._durees
		setups   = data._setups

		# Création du modèle vide
		self._model = pe.ConcreteModel(name="MIP1")
		
		# Création des variables
		self._model.x    =    pe.Var(range(b), range(b), range(m), name="x", bounds=(0,1), domain=pe.Binary) # x_ff'k
		self._model.y    =    pe.Var(range(n), range(m), name='y', bounds=(0,1), domain=pe.Binary)           # y_jk
		self._model.C    =    pe.Var(range(m), name='C', domain=pe.NonNegativeReals)                         # C_k
		self._model.Cmax =    pe.Var(name='Cmax', domain=pe.NonNegativeReals)                                # C_max
		self._model.A    =    pe.Var(range(b), range(m), name='u', domain=pe.NonNegativeReals)               # A_fk
		self._model.u    =    pe.Var(range(b), range(m), name='u', domain=pe.NonNegativeReals)               # u_fk
		
		# Ajout de la fonction objectif au modèle
		self._model.obj = pe.Objective(expr = self._model.Cmax, sense = pe.minimize)
		
		# Ajout des contraintes au modèle
		self._model.contraintes1    = pe.ConstraintList() # Cmax >= Ck pour tout k
		self._model.contraintes2    = pe.ConstraintList() # Ck >= durees des taches lui etant affectees + temps de setup entre familles représentées sur la machine k
		self._model.contraintes3    = pe.ConstraintList() # Le nombre de précédences correspond au nombre de familles représentées sur la machine moins une
		self._model.contraintes4    = pe.ConstraintList() # Si la famille f est représentée sur la machine k on doit en sortir au plus une fois
		self._model.contraintes5    = pe.ConstraintList() # Si la famille f est représentée sur la machine k on doit y entrer au plus une fois
		self._model.contraintes6    = pe.ConstraintList() # Chaque tâche doit être ordonnancée sur exactement une machine
		self._model.contraintes7    = pe.ConstraintList() # Si une tâche est affectée à une machine alors sa famille doit être représentée sur cette machine
		self._model.contraintesX    = pe.ConstraintList() # Contrainte pour forcer la diagonale des variables à être nulles car pas définies
		self._model.contraintesMTZ  = pe.ConstraintList() # Contraintes de sous-tour pour casser les cycles pour la solution
		self._model.contraintesPos  = pe.ConstraintList() # Contraintes avec MTZ pour limiter les positions
		for k in range(m):
			self._model.contraintes1.add(self._model.Cmax >= self._model.C[k])
			self._model.contraintes2.add(self._model.C[k] >= quicksum(durees[j][k] * self._model.y[j,k] for j in range(n)) + quicksum(setups[k][f][f2] * self._model.x[f,f2,k] for f2 in range (b) for f in range(b)))
			self._model.contraintes3.add(quicksum(self._model.x[f,f2,k] for f in range(b) for f2 in range(b)) >= quicksum(self._model.A[f,k] for f in range(b)) - 1)
			for f in range(b):
				self._model.contraintesX.add(self._model.x[f,f,k] == 0)
				self._model.contraintesPos.add(self._model.u[f,k] <= bigM * self._model.A[f,k])
				self._model.contraintes4.add(quicksum(self._model.x[f,f2,k] for f2 in range(b)) <= self._model.A[f,k])
				self._model.contraintes5.add(quicksum(self._model.x[f2,f,k] for f2 in range(b)) <= self._model.A[f,k])
				for f2 in range(b):
					self._model.contraintesMTZ.add(self._model.u[f2,k] >= self._model.u[f,k] + 1 - bigM * (1 - self._model.x[f,f2,k])) 
		
		for j in range(n):
			self._model.contraintes6.add(quicksum(self._model.y[j,k] for k in range(m)) == 1)
			for k in range(m):
				self._model.contraintes7.add(self._model.y[j,k] <= self._model.A[familles[j],k])
				
		
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
			solver.options["MIPGapAbs"] =0.99
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
		# Si le modèle a été résolu à l'optimalité ou si une solution a été trouvée dans le temps limite accordé
		if results.solver.termination_condition==po.TerminationCondition.optimal or results.solver.termination_condition==po.TerminationCondition.maxTimeLimit:
			# Si une solution a été trouvée (optimale ou meilleure solution calculée dans le temps limite accordé)
			print("Solution calculée")
			print("Valeur de la fonction objectif pour la solution retournée: ", pe.value(self._model.obj))
			print("----------------------------------")

			solution=ParallelSchedulingSolution(data._name)
			solution._value=pe.value(self._model.obj)
			for k in range(m):
				premachine = []
				machine = []
				listeChgt = []
				# print(pe.value(self._model.C[k]))
				for f in range(b):
					if (pe.value(self._model.A[f, k]) > 0.5):
						listeChgt.append(f)
				for j in range(n):
					if ((pe.value(self._model.y[j, k]) > 0.5)):
						premachine.append(j)
				for f in listeChgt:
					for j in premachine:
						if (familles[j] == f):
							machine.append(j)
				solution._compoMachine.append(machine)
			return solution




