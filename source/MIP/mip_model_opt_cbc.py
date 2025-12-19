import time
from pyomo.environ import SolverStatus, TerminationCondition
import pyomo.environ as pyo
from pyomo.contrib.solver.common.util import NoFeasibleSolutionError, NoOptimalSolutionError


def tournament_MIP_scheduler(n):
  weeks = n-1
  WEEK = [w for w in range(1, weeks+1)]
  periods = n//2
  PERIOD = [p for p in range(1, periods+1)]
  TEAM = [t for t in range(1, n+1)]
  PAIRS = [(t1, t2) for t1 in TEAM for t2 in TEAM if t1<t2]

  model = pyo.ConcreteModel()

  model.T1 = pyo.Set(initialize=TEAM)
  model.T2 = pyo.Set(initialize=TEAM)
  model.W = pyo.Set(initialize=WEEK)
  model.P = pyo.Set(initialize=PERIOD)
  model.x = pyo.Var(model.T1, model.T2, model.W, model.P,domain=pyo.Binary)

  # to ensure one single match per timeslot (week x period)
  def single_match_per_slot(model, w, p):
    return sum(model.x[t1, t2, w, p] for t1 in model.T1 for t2 in model.T2)==1
  model.single_match_per_slot = pyo.Constraint(model.W, model.P, rule=single_match_per_slot)

  # first problem constraint: each team has to play against each other tean exactly once
  def pair_once(model, t1, t2):
    if t1>=t2: return pyo.Constraint.Skip
    return sum(model.x[t1,t2,w,p] + model.x[t2,t1,w,p] for w in model.W for p in model.P) == 1
  model.pair_once = pyo.Constraint(model.T1, model.T2, rule=pair_once)

  # implied: no team can play against itself
  def no_selfmatch(model, t1, t2, w, p):
    if t1 == t2: return model.x[t1, t2,w,p] == 0
    else: return pyo.Constraint.Skip

  model.no_selfmatch = pyo.Constraint(model.T1, model.T2, model.W, model.P, rule=no_selfmatch)

  # second problem constraint: each team has to play once per week
  def once_a_week(model, t1, w):
    return sum(model.x[t1,t2, w,p] + model.x[t2,t1,w, p] for p in model.P for t2 in model.T2 if t2!=t1) == 1
  model.once_a_week = pyo.Constraint(model.T1, model.W, rule=once_a_week)

  # third problem constraint: each team can play at most twice in the same period
  def max_twice_period(model, t1, p):
    return sum(model.x[t1,t2, w,p] + model.x[t2,t1,w, p] for w in model.W for t2 in model.T2 if t2!= t1) <= 2
  model.max_twice_period = pyo.Constraint(model.T1, model.P, rule=max_twice_period)


  #symmetry break: fix first diagonal matches
  def first_diag_match(model, p):
    return model.x[2*p-1, 2*p, p, p] == 1
  model.first_diag_match = pyo.Constraint(model.P,rule=first_diag_match)

  # function to be optimized (absolute value has to be linearized)
  #  to store home and away counts
  def home_t(model, t1):
    return sum(model.x[t1,t2, w,p] for w in model.W for p in model.P for t2 in model.T2 if t2!=t1)
  def away_t(model, t1):
    return sum(model.x[t2,t1, w,p] for w in model.W for p in model.P for t2 in model.T2 if t2!=t1)

  # auxiliary variable
  model.abs_diff = pyo.Var(model.T1,domain=pyo.NonNegativeReals)

  # if module argument is >= 0
  def linearize_abs_diff_1(model, t1):
    return home_t(model, t1) - away_t(model, t1) <= model.abs_diff[t1]
  model.linearize_abs_diff_1 = pyo.Constraint(model.T1, rule=linearize_abs_diff_1)

  # if module argument is < 0
  def linearize_abs_diff_2(model, t1):
    return home_t(model, t1) - away_t(model, t1) >= - model.abs_diff[t1]
  model.linearize_abs_diff_2 = pyo.Constraint(model.T1, rule=linearize_abs_diff_2)

  # sum of auxiliary variable values
  def opt_func(model):
    return sum(model.abs_diff[t1] for t1 in model.T1)

  # optimization objective: minimize sum of auxiliary variable values
  # -> minimize home/ away difference
  model.obj = pyo.Objective(rule=opt_func, sense=pyo.minimize)

  # solver_h = pyo.SolverFactory('highs')
  # solver_h.options['threads'] = 1
  # solver_h.options['time_limit'] = 300
  # result_h = solver_h.solve(model, tee=True)

  solver_c = pyo.SolverFactory('cbc')
  solver_c.options['threads'] = 1
  solver_c.options['seconds'] = 300

  try:
    start = time.time()
    result_c = solver_c.solve(model)
    elapsed = int(time.time()-start)
  except NoFeasibleSolutionError:
    elapsed = int(time.time()-start) #unsat case (before timeout)
    #print("The problem is infeasible.")
    return {"time":elapsed, "optimal":True, "obj":None, "sol":[]}
  # except NoOptimalSolutionError:
  #   print("Timeout")



  tc = result_c.solver.termination_condition
  st = result_c.solver.status

  schedule = []

  if tc == TerminationCondition.optimal:
      # Optimal solution, safe to read
      optimal = True
      for p in model.P:
          period_list = []
          for w in model.W:
              for t1 in model.T1:
                  for t2 in model.T2:
                      if t1 >= t2: continue
                      if pyo.value(model.x[t1,t2,w,p]) > 0.1:
                          period_list.append([t1,t2])
                      elif pyo.value(model.x[t2,t1,w,p]) > 0.1:
                          period_list.append([t2,t1])
          schedule.append(period_list)
      obj_value = int(model.obj())

  elif tc == TerminationCondition.maxTimeLimit:
      # Timeout: only use solution if it exists
      elapsed = 300
      optimal = False
      exists_sol = any(v.value is not None for v in model.component_data_objects(pyo.Var))
      if exists_sol:
          for p in model.P:
              period_list = []
              for w in model.W:
                  for t1 in model.T1:
                      for t2 in model.T2:
                          if t1 >= t2: continue
                          val = pyo.value(model.x[t1,t2,w,p])
                          if val is not None and val > 0.1:
                              period_list.append([t1,t2])
                          elif val is not None and pyo.value(model.x[t2,t1,w,p]) > 0.1:
                              period_list.append([t2,t1])
              schedule.append(period_list)
          obj_value = int(model.obj())
      else:
          schedule = []
          obj_value = None

  elif tc == TerminationCondition.infeasible:
      # Infeasible → no solution
      optimal = True
      schedule = []
      obj_value = None

  else:
      # Any other termination → treat as timeout without solution
      print("Warning: TerminationCondition = ", tc)
      if elapsed > 300: elapsed = 300
      optimal = False
      schedule = []
      obj_value = None
  return {"time":elapsed, "optimal":optimal, "obj":obj_value, "sol":schedule}

if __name__ == "__main__":
  n = int(input())
  schedule = tournament_MIP_scheduler(n)