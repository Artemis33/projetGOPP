from ParallelSchedulingData import *
from ParallelSchedulingSolution import *
import math
import pyomo.environ as pe 
import pyomo.opt as po
from pyomo.core import quicksum

class ParallelSchedulingBenders:
	def __init__(self):
		"""
		Initialize the scheduler with the model to solve the Parallel Scheduling Problem.
		"""
		self._model = None

		def RPM(self, data: ParallelSchedulingData, solverName='gurobi', timeLimit, verbose=False):
		"""
		Solves the Base of the Master Problem version of self._model for the problem.

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
		familles = data._familles
		durees   = data._durees
		setups   = data._setups

		# Création du modèle vide
		self._model = pe.ConcreteModel(name="PMbase")
		
		# Création des variables
		self._model.z     =    pe.Var(range(n), range(m), name='z', bounds=(0,1), domain=pe.Binary)           # z_jk
		self._model.theta =    pe.Var(range(m), name='pi', domain=pe.NonNegativeReals)                        # theta_k
		self._model.Cmax  =    pe.Var(name='Cmax', domain=pe.NonNegativeReals)                                # C_max

		# Fonction objectif 
		self._model.obj = pe.Objective(expr = self._model.Cmax, sense = pe.minimize)

		# Contraintes
		self._model.contraintes1 = pe.ConstraintList()
		for j in range(n):
			self._model.contraintes1.add(quicksum(self._model.z[j,k] for k in range(m)) == 1)
		instance = self._model.create_instance()
		return instance



	def Phi(data: ParallelSchedulingData, z, k, solverName='gurobi', verbose=False, timeLimit=600):
		"""
		z : indices des tâches qu'on garde
		k : machine sur laquelle on travaille
		"""
		# On met les données avec les notations du problème
		n = data._nbJob
		m = data._nbMachine
		b = data._nbFamille
		bigM = len(z)
		
		# On récupère les données individuelles 
		familles = data._familles
		durees	 = [data._durees[j][k] for j in range(n)]
		setups 	 = [data._setups[f][f2][k] for f in range(b) for f2 in range(b)]
		durees.append(0)

		SP = pe.ConcreteModel(name="SP")
		SP.x = pe.Var(range(n+1), range(n), name='x', bounds=(0,1), domain=pe.Binary)
		SP.u = pe.Var(range(n+1), name='u', domain=pe.NonNegativeReals)
		SP.Cmax = pe.Var(name='C_max', domain=pe.NonNegativeReals)

		# Définition de la fonction objectif
		SP.obj = pe.Objective(expr = SP.Cmax, sense = pe.minimize)

		# Ajout des contraintes
		SP.contraintes1 = pe.ConstraintList()
		SP.contraintes2 = pe.ConstraintList()
		SP.contraintes3 = pe.ConstraintList()
		SP.contraintes4 = pe.ConstraintList()
		SP.contraintes5 = pe.ConstraintList()
		SP.contraintesX = pe.ConstraintList()
		for i in range(n):
			for j in range(n):
				if (not(i in z) or not(j in z)):
					SP.contraintes1.add(SP.x[i,j] == 0)
		for i in range(n):
			SP.contraintesX.add(SP.x[i,i] == 0)
			SP.contraintes2.add(SP.u[i] <= bigM)
			SP.contraintes3.add(quicksum(SP.x[i,j] for j in range(n)) == quicksum(SP.x[j,i] for j in range(n)))
			SP.contraintes5.add(quicksum(SP.x[j,i] for j in range(n)) == 1)
			for j in range(n+1):
				SP.contraintes4.add(SP.u[j] >= SP.u[i] + 1 - bigM * (1 - SP.x[i,j]))
		SP.contrainte5 = pe.Constraint( expr = SP.Cmax >= quicksum( (durees[j] + setups[familles[i]][familles[j]]) * SP.x[i,j] for i in range(n) for j in range(n)) + quicksum(durees[j]*x[n,j] for j in range(n)) )
		SP.contrainte6 = pe.Constraint( expr = SP.u[n] == 0)
		SP.contrainte7 = pe.Constraint( expr = quicksum(model.x[n,j]) == 1)

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
		results = solver.solve(SP,tee=False)
		if results.solver.termination_condition==po.TerminationCondition.optimal or results.solver.termination_condition==po.TerminationCondition.maxTimeLimit:
			return pe.value(SP.obj)


def check_optimality_1(m, z, theta):
	obj, alpha, beta = DualSP(m, z)
	if(obj < theta):
		return True, alpha, beta
	else:
		return False, alpha, beta

	
def Benders(data: ParallelSchedulingData):
	stop = False
	K = data._nbScenar
	XI = data._scenarios
	PM1, x, theta = PM1_base(data)
	indices = [(arc[0], arc[1]) for arc in data._arcs]
	Dopt = []
	iter = 0
	while(stop==False) and (iter <= 50):
		# print("Benders")
		stop = True
		PM1, x, theta, Gap = PM_cuts(PM1, x, theta, data, Dopt, iter)
		Dopt = []
		for xi in range(K):
			T = {(i,j):0 for (i,j) in indices}
			for (i,j) in XI[xi]:
				T[(i,j)] = 1
			# print(f"x:{x}, ksi:{ksi[k]}, theta:{theta[k]}")
			optim, mu, l = check_optimality_1(data, theta[xi].X, x, T)
			#print(mu,l)
			# print(f"mu:{mu}")
			if (optim):
				stop = False
				Dopt.append([mu, l, xi])
		iter += 1
	print("end")
	solution = KEPsolution(data._name, "Benders_1")
	values = []
	gaps = []
	for xi in range(K):
		T = {(i,j):0 for (i,j) in indices}
		for (i,j) in XI[xi]:
			T[(i,j)] = 1
		obj, gap,_, _, listCycles = SP_1(data, x, T)
		values.append(obj)
		gaps.append(gap)
		solution._cycleCompo.append(listCycles)
	solution._value = PM1.ObjVal
	solution._Gap = Gap
	std_dev, std_dev_gap = compute_std_deviation(solution._value, values, gaps, data, x)
	solution._IC_value, solution._IC_gap = conf_inter(solution._value, solution._Gap, std_dev, std_dev_gap, K)
	return solution


def PM_cuts(instance, data : KEPdata, Dopt, iter):
	# print("PM cuts")
	# PM.update()
	# PM.optimize()
	# UB = PM.ObjVal               # Borne supérieure : valeur de la solution courante
	# LB = PM.ObjBound             # Borne inférieure : meilleure borne duale connue
	# return PM, x, theta

# def DualSP(m, z, solverName='gurobi', verbose=False, timeLimit=600):
# 	DSP = pe.ConcreteModel(name="DSP")
# 	DSP.a = pe.Var(range(m), name='alpha', domain=pe.NonNegativeReals)
# 	DSP.b = pe.Var(range(m), name='beta', domain=pe.NonNegativeReals)

# 	# Définition de la fonction objectif
# 	DSP.obj = pe.Objective(expr = DSP.Cmax, sense = pe.maximize)

# 	# Ajout des contraintes
# 	DSP.contraintes1 = pe.ConstraintList()
# 	DSP.contraintes2 = pe.ConstraintList()
# 	for k in range(m):
# 		DSP.contraintes1.add(DSP.a[k] - DSP.b[k] <= 0)
# 		DSP.contraintes1.add(DSP.b[k] <= 1)

# 	solver_name = solverName
# 	if po.SolverFactory(solver_name).available():
# 		print("Solver " + solver_name + " is available.")
# 	else:
# 		print("Solver " + solver_name + " is not available.")
# 	solver = po.SolverFactory(solver_name)
# 	if solver_name == 'appsi_highs':
# 		solver.options['time_limit'] = timeLimit
# 		solver.options['mip_rel_gap'] = 1e-6
# 		solver.options['mip_abs_gap'] = 0.99
# 	elif solver_name == 'cbc':
# 		solver.options['seconds'] = timeLimit
# 		solver.options['ratioGap'] = 1e-4
# 		solver.options['allowableGap'] = 0.99
# 	elif solver_name == 'gurobi':
# 		solver = po.SolverFactory(solver_name, solver_io="python")
# 		solver.options["TimeLimit"] = timeLimit
# 		solver.options["MIPGap"] = 1e-4
# 		solver.options["MIPGapAbs"] = 0.99
# 	results = solver.solve(self._model,tee=False)
# 	alpha, beta = [], []
# 	for k in range(m):
# 		alpha.append(pe.value(DSP.a[k]))
# 		beta.append(pe.value(DSP.b[k]))
# 	valeur = pe.value(self._model.obj)
# 	return valeur, alpha, beta