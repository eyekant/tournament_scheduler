from minizinc import Model, Solver, Instance, Status
import time
from datetime import timedelta
from pathlib import Path

def tournament_CP_scheduler(n):
    model_path = Path(__file__).parent / "local_noimplied_gecode.mzn"
    model = Model(str(model_path.resolve()))    
    solver = Solver.lookup("gecode")
    instance = Instance(solver, model)
    instance["n"] = n
    start = time.time()
    result = instance.solve(timeout=timedelta(seconds=300))
    elapsed = int(time.time()-start)
    if result.status.has_solution():
        schedule = []
        weeks = n -1
        periods = n//2
        tHome = result["tHome"]
        tAway = result["tAway"]
        for i in range(periods):
            period_list = []
            for j in range(weeks):
                home_team = int(tHome[i][j])
                away_team = int(tAway[i][j])
                period_list.append([home_team, away_team])
            schedule.append(period_list)
        obj_val = None
        if result.status == Status.SATISFIED:
            #print("Feasible solution found:")
            return {"time":elapsed, "optimal":True, "obj":obj_val, "sol":schedule}
        elif result.status == Status.OPTIMAL_SOLUTION:
            #print("Optimal solution found:")
            return {"time":elapsed, "optimal":True, "obj":obj_val, "sol":schedule}
    if result.status == Status.UNSATISFIABLE:
        #print("The problem is unsat.")
        return {"time":elapsed, "optimal":True, "obj":None, "sol":[]}
    else: #solver timed out
        #print("The solver has timed out without finding a feasible solution.")
        return {"time":300, "optimal":False, "obj":None, "sol":[]}



if __name__=="__main__":
    n = int(input())
    results = tournament_CP_scheduler(n)