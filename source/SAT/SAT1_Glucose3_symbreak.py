from z3 import *
from itertools import combinations
import pandas as pd
from pysat.solvers import Glucose3
import time

# Define the variables
teams = 6
number_of_weeks = teams-1
number_of_periods = teams//2

# Utils
# Display the tournament schedule as a table with dimensions [number_of_periods x number_of_weeks]
def display_tournament(sol):
  table = []
  if sol is None:
    return None
  for (team1, team2, week, period) in sol:
    table.append({
          'Week': week,
          'Period': period,
          'Match': f"{team1} vs {team2}"})

  df = pd.DataFrame(table)
  table = df.pivot(index='Period', columns='Week', values='Match')
  table.columns = ['Week ' + str(i) for i in table.columns]
  table.index = ['Period ' + str(i) for i in table.index]
  print(table)

# Cardinality constraint for Glucose3
def at_least_one(int_vars):
    return int_vars

def at_most_one(int_vars):
  clauses = []
  for v1,v2 in combinations(int_vars, 2):
    clauses.append([-v1,-v2])
  return clauses

def exactly_one(int_vars):
    return at_most_one(int_vars) + [at_least_one(int_vars)]

def at_most_k(int_vars, k):
    clauses = []
    for X in combinations(int_vars, k+1):
      clause = [-v for v in X]
      clauses.append(clause)
    return clauses

# Generate a SAT model to solve the tournament scheduling problem, using the Glucose3 solver and some symmetry breaking constraints to reduce the
# search space and improve the overall solver efficiency
def tournament_SAT_scheduler(teams):
  # Check that the number of teams is even
  if teams % 2 != 0:
    print("Input error: n must be even.")

  number_of_weeks = teams-1
  number_of_periods = teams//2

  # Map the Boolean variables games[x,y,z,p] to unique integer variables required by the Minisat solver.
  # Variables are created only for valid games (x!=y), since a team cannot play against itself
  varnum = 1
  var_map = {}
  for x in range(teams):
    for y in range(teams):
      if x!=y:
        for w in range(number_of_weeks):
          for p in range(number_of_periods):
            var_map[(x,y,w,p)] = varnum
            varnum += 1

  games = [[[[None if x==y else var_map[(x,y,w,p)]
                for p in range(number_of_periods)]
                for w in range(number_of_weeks)]
                for y in range(teams)]
                for x in range(teams)]

  # Initialize the Glucose3 solver
  s = Glucose3() 

  # Constraint: each team plays against each other team exactly once, regardless of which team plays at home or away
  for x in range(teams):
    for y in range(x+1,teams):
      to_add = [games[x][y][z][p]for z in range(number_of_weeks) for p in range(number_of_periods)if games[x][y][z][p] is not None]
      for clause in exactly_one(to_add):
        s.add_clause(clause)

  # Symmetry breaking constraint: fix the first week (index 0) matches
  for p in range(number_of_periods):
    s.add_clause([games[p][p+number_of_periods][0][p]])

  # Constraint: in each week and period only one match is scheduled, ensuring no overlapping between games
  for z in range(number_of_weeks):
    for p in range(number_of_periods):
      to_add = [games[x][y][z][p]for x in range(teams)for y in range(teams)if games[x][y][z][p] is not None]
      for clause in exactly_one(to_add):
        s.add_clause(clause)

  # Constraint: each team plays at most twice in the same period
  for p in range(number_of_periods):
    for x in range(teams):
      matches = []
      for z in range(number_of_weeks):
        for y in range(teams):
          if games[x][y][z][p] is not None:
              matches.append(games[x][y][z][p]) # Case in which team x plays at home against team y
          if games[y][x][z][p] is not None:
              matches.append(games[y][x][z][p]) # Opposite case, team y plays at home against team x
      for clause in at_most_k(matches,2):
        s.add_clause(clause)

  # Constraint: each team plays once a week, either at home or away
  for x in range(teams):
    for z in range(number_of_weeks):
      games_per_team = [games[x][y][z][p] for y in range(teams) for p in range(number_of_periods)if games[x][y][z][p] is not None]+\
      [games[y][x][z][p]for y in range(teams)for p in range(number_of_periods) if games[y][x][z][p] is not None]
      for clause in exactly_one(games_per_team):
          s.add_clause(clause)

  start = time.time()
  sat = s.solve()
  elapsed = int(time.time()-start)

  # Check satisfiability
  if sat:
    m = s.get_model()
    #print("SAT")
    sol = [(x+1, y+1, z+1, p+1) for x in range(teams) for y in range(teams) \
               for z in range(number_of_weeks) for p in range(number_of_periods) if games[x][y][z][p] is not None and games[x][y][z][p] in m]
    
    # Output to be saved in json files
    matrix = [[None for _ in range(number_of_weeks)] for _ in range(number_of_periods)]
    for team1, team2, w, p in sol:
      matrix[p-1][w-1] = [team1, team2]

    # for p in range(number_of_periods):
    #   if p != (teams // 2 -1):     
    #     print(f"{matrix[p]},")
    #   else:
    #     print(matrix[p])

    return {"time":elapsed, "optimal":True, "obj": None, "sol":matrix}
  elif sat == False: # proved unsatisfiable
    #print("UNSAT")
    return {"time":elapsed, "optimal":True, "obj":None, "sol":[]}
  else: #timed out with no solution (remember: no optimality possible)
    # print("UNSAT")
    # print("The solver has timed out without finding a feasible solution.")
    return {"time":300, "optimal":False, "obj":None, "sol":[]}


if __name__ == "__main__":
  teams = int(input())
  # Generate the tournament schedule and display the output
  sol = tournament_SAT_scheduler(teams)
  display_tournament(sol)