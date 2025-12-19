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
          'Week': week+1,
          'Period': period+1,
          'Match': f"{team1+1} vs {team2+1}"})

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
    print("Input error: n must be even")
    return None
  
  number_of_weeks = teams-1
  number_of_periods = teams//2
  
  # Build the Boolean variables is_home[x,w,p] and is_away[x,w,p]
  # is_home[x,w,p] is True if team x plays at home in week w and period p
  is_home = [[[Bool(f"is_home_{x+1}_{w+1}_{p+1}") for p in range(number_of_periods)] for w in range(number_of_weeks)]for x in range(teams)]
  # is_away[x,w,p] is True if team x plays away in week w and period p
  is_away = [[[Bool(f"is_away_{x+1}_{w+1}_{p+1}") for p in range(number_of_periods)] for w in range(number_of_weeks)]for x in range(teams)]
  
  # Initialize the Z3 solver
  s = Solver()

  # Set the time limit to 5 minutes
  s.set("timeout",300000) 

  # Constraint: consider only valid games by forbidding a team from being both at home and away in the same week and period
  for x in range(teams):
    for w in range(number_of_weeks):
      for p in range(number_of_periods):
        s.add(Not(And(is_home[x][w][p],is_away[x][w][p])))

  # Constraint: each team plays against each other team exactly once, regardless of which team plays at home or away
  for x in range(teams):
    for y in range(x+1,teams):
      matches = []
      for w in range(number_of_weeks):
        for p in range(number_of_periods):
          match1 = And(is_home[x][w][p],is_away[y][w][p])
          match2 = And(is_home[y][w][p],is_away[x][w][p])
          matches.append(Or(match1,match2))
      s.add(exactly_one(matches))

  # Constraint: in each week and period only one match is scheduled, ensuring no overlapping between games
  for w in range(number_of_weeks):
    for p in range(number_of_periods):
      matches = []
      for x in range(teams):
        for y in range(teams):
          if x!=y:
            matches.append(And(is_home[x][w][p],is_away[y][w][p]))
      s.add(exactly_one(matches))

  # Constraint: each team plays at most twice in the same period
  for p in range(number_of_periods):
    for x in range(teams):
      matches = []
      for w in range(number_of_weeks):
        matches.append(is_home[x][w][p])
        matches.append(is_away[x][w][p])
      s.add(at_most_k(matches,2))

  # Constraint: each team plays once a week, either at home or away
  for x in range(teams):
    for w in range(number_of_weeks):
      matches = []
      for p in range(number_of_periods):
        matches.append(is_home[x][w][p])
        matches.append(is_away[x][w][p])
      s.add(exactly_one(matches))

  # Check satisfiability
  start = time.time()
  sat_check = s.check()
  elapsed = int(time.time()-start)
  if sat_check == sat:
    m = s.model()
    #print("SAT")
    schedule = []
    for w in range(number_of_weeks):
      for p in range(number_of_periods):
        for x in range(teams):
          if m.evaluate(is_home[x][w][p])==True:
            for y in range(teams):
              if m.evaluate(is_away[y][w][p])==True:
                schedule.append((x,y,w,p))
    matrix = [[None for _ in range(number_of_weeks)] for _ in range(number_of_periods)]
    for team1, team2, w, p in schedule:
        matrix[p][w] = [team1+1, team2+1]
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