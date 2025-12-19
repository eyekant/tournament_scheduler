from z3 import *
import pandas as pd
from itertools import combinations
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

# Cardinality constraint: at least one variable is True
def at_least_one(bool_vars):
    return Or(bool_vars)

# Cardinality constraint: at most one variable is True
def at_most_one(bool_vars):
    return And([Not(And(pair[0], pair[1])) for pair in combinations(bool_vars, 2)])

# Cardinality constraint: exactly one variable is True
def exactly_one(bool_vars):
    return And(at_least_one(bool_vars), at_most_one(bool_vars))

# Cardinality constraint: at most k variables are True
def at_most_k(bool_vars, k):
    return And([Or([Not(x) for x in X]) for X in combinations(bool_vars, k + 1)])

# Generate a SAT model to solve the tournament scheduling problem, using the Z3 solver
def tournament_SAT_scheduler(teams):
  # Check that the number of teams is even
  if teams % 2 != 0:
    print("Input error: n must be even.")

  number_of_weeks = teams-1
  number_of_periods = teams//2

  # Build the Boolean variables games[x,y,z,p], meaning that team x plays at home against team y in week z and period p
  # Variables are created only for valid games (x!=y), since a team cannot play against itself
  games = [[[[None if x==y else Bool(f"Game_{x+1}_{y+1}_{z+1}_{p+1}") 
                for p in range(number_of_periods)]
                for z in range(number_of_weeks)]
                for y in range(teams)]
                for x in range(teams)]

  # Initialize the Z3 solver
  s = Solver()

  # Set the time limit to 5 minutes
  s.set("timeout",300000) 

  # Constraint: each team plays against each other team exactly once, regardless of which team plays at home or away
  for x in range(teams):
    for y in range(x+1,teams):
      valid_matches = [games[x][y][z][p] for z in range(number_of_weeks) for p in range(number_of_periods) if games[x][y][z][p] is not None] +\
       [games[y][x][z][p] for z in range(number_of_weeks) for p in range(number_of_periods)if games[y][x][z][p] is not None]
      s.add(exactly_one(valid_matches))

  # Constraint: in each week and period only one match is scheduled, ensuring no overlapping between games
  for z in range(number_of_weeks):
    for p in range(number_of_periods):
      matches = [games[x][y][z][p] for x in range(teams) for y in range(teams) if games[x][y][z][p] is not None]
      s.add(exactly_one(matches))

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
      s.add(at_most_k(matches, 2))

  # Constraint: each team plays once a week, either at home or away
  for x in range(teams):
    for z in range(number_of_weeks):
      matches = []
      for y in range(teams):
        for p in range(number_of_periods):
          if games[x][y][z][p] is not None:
            matches.append(games[x][y][z][p])
          if games[y][x][z][p] is not None:
            matches.append(games[y][x][z][p])
      s.add(exactly_one(matches))

  # Check satisfiability
  start = time.time()
  sat_check = s.check()
  elapsed = int(time.time()- start)
  if sat_check == sat:
    m = s.model()
    # print("SAT")
    # print("Solution found:")
    sol = [(x+1, y+1, z+1, p+1) for x in range(teams) for y in range(teams) \
               for z in range(number_of_weeks) for p in range(number_of_periods) if games[x][y][z][p] is not None and m.evaluate(games[x][y][z][p])==True]
    
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
  elif sat_check == unsat:
      #print("UNSAT")
      return {"time":elapsed, "optimal":True, "obj":None, "sol":[]}
  elif sat_check == unknown:
      return {"time":300, "optimal":False, "obj":None, "sol":[]}

if __name__ == "__main__":
  teams = int(input())
  # Generate the tournament schedule and display the output
  sol = tournament_SAT_scheduler(teams)
  display_tournament(sol)