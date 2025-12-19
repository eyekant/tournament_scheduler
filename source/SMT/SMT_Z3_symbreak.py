from z3 import *
import pandas as pd
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
          'Match': f"{team1} vs {team2}"
    })

  df = pd.DataFrame(table)
  table = df.pivot(index='Period', columns='Week', values='Match')
  table.columns = ['Week ' + str(i) for i in table.columns]
  table.index = ['Period ' + str(i) for i in table.index]
  print(table)
  
# Generate a SMT model to solve the tournament scheduling problem, using the Z3 solver and some symmetry breaking constraints to reduce the
# search space and improve the overall solver efficiency
def tournament_SMT_scheduler(teams):
  # Check that the number of teams is even
  if teams % 2 != 0:
    print("Input error: n must be even")
    return None

  number_of_weeks = teams-1
  number_of_periods = teams//2

  # Define integer variables to represent the teams involved in each match
  # home_team[w][p] is the team playing at home in week w and period p
  home_team = [[Int(f"hometeam_{w+1}_{p+1}") for p in range(number_of_periods)] for w in range(number_of_weeks)]
  # away_team[w][p] is the team playing away in week w and period p
  away_team = [[Int(f"awayteam_{w+1}_{p+1}") for p in range(number_of_periods)] for w in range(number_of_weeks)]
  
  # Initialize the Z3 solver
  s = Solver()

  # Set the time limit to 5 minutes
  s.set("timeout",300000) 

  # Specify the domains of home and away teams and prevent a team playing against itself
  for w in range(number_of_weeks):
    for p in range(number_of_periods):
      s.add(And(home_team[w][p] >= 1, home_team[w][p] <= teams))
      s.add(And(away_team[w][p] >= 1, away_team[w][p] <= teams))
      s.add(home_team[w][p]!=away_team[w][p])
      s.add(home_team[w][p]< away_team[w][p]) # Symmetry breaking constraint: lexicographical ordering between home and away teams

  # Constraint: each team plays against each other team exactly once, regardless of which team plays at home or away
  for x in range(1,teams+1):
    for y in range(x+1,teams+1):
      s.add(Sum([
          If(And(home_team[w][p]==x, away_team[w][p]==y),1,0)+If(And(home_team[w][p]==y, away_team[w][p]==x),1,0)
          for w in range(number_of_weeks)for p in range(number_of_periods)])==1)

  # Symmetry breaking constraint: fix the first week (index 0) matches
  for p in range(number_of_periods):
    s.add(home_team[0][p]==p+1)
    s.add(away_team[0][p]==p+1+number_of_periods)

  # Symmetry breaking constraint: lexicographical ordering between columns (weeks)
  for w in range(number_of_weeks-1):
    constraint = []
    for p in range(number_of_periods):
      equal = And([
          And(home_team[w][k]==home_team[w+1][k],away_team[w][k]==away_team[w+1][k]) for k in range(p)])
      less = Or(home_team[w][p]<home_team[w+1][p],And(home_team[w][p]==home_team[w+1][p],away_team[w][p]<away_team[w+1][p]))
      constraint.append(Implies(equal,less))
    s.add(Or(constraint))

  # Constraint: each team plays at most twice in the same period
  for p in range(number_of_periods):
    for x in range(1,teams+1):
      s.add(Sum([
          If(home_team[w][p]==x,1,0)+If(away_team[w][p]==x,1,0)
          for w in range(number_of_weeks)])<=2)

  # Constraint: each team plays once a week, either at home or away
  for w in range(number_of_weeks):
    all_teams = [home_team[w][p] for p in range(number_of_periods)] + [away_team[w][p] for p in range(number_of_periods)]
    s.add(Distinct(all_teams))

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
        team1 = m.evaluate(home_team[w][p]).as_long()
        team2 = m.evaluate(away_team[w][p]).as_long()
        schedule.append((team1,team2,w,p))
    matrix = [[None for _ in range(number_of_weeks)] for _ in range(number_of_periods)]
    for team1, team2, w, p in schedule:
        matrix[p][w] = [team1, team2]
    # for p in range(number_of_periods):
    #   if p != (teams // 2 -1):     
    #     print(f"{matrix[p]},")
    #   else:
    #     print(matrix[p])
    return {"time": elapsed, "optimal": True, "obj":None, "sol":matrix}
  elif sat_check == unsat:
    #print("UNSAT")
    return {"time": elapsed, "optimal": True, "obj":None, "sol":[]}
  else: #timed out
    return {"time": 300, "optimal": False, "obj":None, "sol":[]}

if __name__ == "__main__":
  teams = int(input())
  # Generate the tournament schedule and display the output
  sol = tournament_SMT_scheduler(teams)
  display_tournament(sol)