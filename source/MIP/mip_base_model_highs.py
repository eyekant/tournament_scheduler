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
  # -> introduce a non-integer variable tp that stores the sum per period and team
  model.tp = pyo.Var(model.T1, model.P, domain=pyo.NonNegativeReals)
    
  def sum_period_team(model, t1, p):
    return model.tp[t1, p] == sum(model.x[t1,t2, w,p] + model.x[t2,t1,w, p] for w in model.W for t2 in model.T2 if t2!= t1)
  model.sum_period_team = pyo.Constraint(model.T1, model.P, rule=sum_period_team)
  #apply the constraint to the variable tp
  def max_twice_tp_relaxed(model, t1, p):
    return model.tp[t1, p] <= 2
  model.max_twice_tp_relaxed = pyo.Constraint(model.T1, model.P, rule=max_twice_tp_relaxed)

  model.obj = pyo.Objective(expr=0, sense=pyo.minimize)

  solver_h = pyo.SolverFactory('highs')
  solver_h.options['threads'] = 1
  solver_h.options['time_limit'] = 300
  try:
    start = time.time()
    result_h = solver_h.solve(model)
    elapsed = int(time.time()-start)
  except NoFeasibleSolutionError:
    elapsed = int(time.time()-start) #unsat case (before timeout)
    #print("The problem is infeasible.")
    return {"time":elapsed, "optimal":True, "obj":None, "sol":[]}
  # except NoOptimalSolutionError:
  #   print("Timeout")

  tc = result_h.solver.termination_condition
  st = result_h.solver.status
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
      else:
          schedule = []

  elif tc == TerminationCondition.infeasible:
      # Infeasible → no solution
      optimal = True
      schedule = []

  else:
      # Any other termination → treat as timeout without solution
      print("Warning: TerminationCondition = ", tc)
      if elapsed > 300: elapsed = 300
      optimal = False
      schedule = []

  return {"time":elapsed, "optimal":optimal, "obj":None, "sol":schedule}

if __name__ == "__main__":
  n = int(input())
  schedule = tournament_MIP_scheduler(n) 