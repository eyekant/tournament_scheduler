#import sys
import time, json
from pathlib import Path

# Import the needed solvers
from SAT.SAT1_Z3 import tournament_SAT_scheduler as z3_1
from SAT.SAT1_Z3_symbreak import tournament_SAT_scheduler as z3_1_symbreak
from SAT.SAT1_Minisat22 import tournament_SAT_scheduler as minisat22_1
from SAT.SAT1_Minisat22_symbreak import tournament_SAT_scheduler as minisat22_1_symbreak
from SAT.SAT1_Glucose3 import tournament_SAT_scheduler as glucose3_1
from SAT.SAT1_Glucose3_symbreak import tournament_SAT_scheduler as glucose3_1_symbreak
from SAT.SAT2_Z3 import tournament_SAT_scheduler as z3_2
from SAT.SAT2_Z3_symbreak import tournament_SAT_scheduler as z3_2_symbreak
from SMT.SMT_Z3 import tournament_SMT_scheduler as z3
from SMT.SMT_Z3_symbreak import tournament_SMT_scheduler as z3_symbreak
from SMT.SMT_opt import tournament_SMT_scheduler as z3_opt
from SMT.SMT_opt_symbreak import tournament_SMT_scheduler as z3_opt_symbreak
from MIP.mip_base_model_cbc import tournament_MIP_scheduler as solve_base_cbc
from MIP.mip_base_model_opt_cbc import tournament_MIP_scheduler as solve_base_opt_cbc
from MIP.mip_model_cbc import tournament_MIP_scheduler as solve_symbreak_cbc
from MIP.mip_model_opt_cbc import tournament_MIP_scheduler as solve_symbreak_opt_cbc
from MIP.mip_base_model_highs import tournament_MIP_scheduler as solve_base_highs
from MIP.mip_base_model_opt_highs import tournament_MIP_scheduler as solve_base_opt_highs
from MIP.mip_model_highs import tournament_MIP_scheduler as solve_symbreak_highs
from MIP.mip_model_opt_highs import tournament_MIP_scheduler as solve_symbreak_opt_highs
from CP.basic_chuffed import tournament_CP_scheduler as basic_chuffed
from CP.local_symbreak_chuffed import tournament_CP_scheduler as local_symbreak_chuffed
from CP.global_symbreak_chuffed import tournament_CP_scheduler as global_symbreak_chuffed
from CP.global_symbreak_opt_chuffed import tournament_CP_scheduler as global_symbreak_opt_chuffed
from CP.basic_gecode import tournament_CP_scheduler as basic_gecode
from CP.local_symbreak_gecode import tournament_CP_scheduler as local_symbreak_gecode
from CP.global_symbreak_gecode import tournament_CP_scheduler as global_symbreak_gecode
from CP.global_symbreak_opt_gecode import tournament_CP_scheduler as global_symbreak_opt_gecode
from CP.local_noimplied_chuffed import tournament_CP_scheduler as local_noimplied_chuffed
from CP.local_noimplied_gecode import tournament_CP_scheduler as local_noimplied_gecode


# Associate each approach with its solver
SOLVERS = {
    "Z3_1": z3_1,
    "Z3_1_symbreak": z3_1_symbreak,
    "MINISAT22_1": minisat22_1,
    "MINISAT22_1_symbreak": minisat22_1_symbreak,
    "GLUCOSE3_1": glucose3_1,
    "GLUCOSE3_1_symbreak": glucose3_1_symbreak,
    "Z3_2": z3_2,
    "Z3_2_symbreak": z3_2_symbreak,
    "smt_Z3": z3,
    "smt_Z3_symbreak": z3_symbreak,
    "smt_Z3_optimize": z3_opt,
    "smt_Z3_optimize_symbreak": z3_opt_symbreak,
    "basic_gecode": basic_gecode,
    "local_symbreak_gecode": local_symbreak_gecode,
    "local_noimplied_gecode": local_noimplied_gecode,
    "global_symbreak_gecode": global_symbreak_gecode,
    "global_symbreak_opt_gecode": global_symbreak_opt_gecode,
    "basic_chuffed": basic_chuffed,
    "local_symbreak_chuffed": local_symbreak_chuffed,
    "local_noimplied_chuffed": local_noimplied_chuffed,
    "global_symbreak_chuffed": global_symbreak_chuffed,
    "global_symbreak_opt_chuffed": global_symbreak_opt_chuffed,
    "base_cbc": solve_base_cbc,
    "base_opt_cbc": solve_base_opt_cbc,
    "symbreak_cbc": solve_symbreak_cbc,
    "symbreak_opt_cbc": solve_symbreak_opt_cbc,
    "base_highs": solve_base_highs,
    "base_opt_highs": solve_base_opt_highs,
    "symbreak_highs": solve_symbreak_highs,
    "symbreak_opt_highs": solve_symbreak_opt_highs,
}

# Associate each approach with increasing number of teams until it times out
VALID_TEAMS = {
    "Z3_1": {4, 6, 8},
    "Z3_1_symbreak": {4, 6, 8},
    "MINISAT22_1": {4, 6, 8, 10},
    "MINISAT22_1_symbreak": {4, 6, 8, 10},
    "GLUCOSE3_1": {4, 6, 8, 10},
    "GLUCOSE3_1_symbreak": {4, 6, 8, 10},
    "Z3_2": {4, 6, 8, 10, 12},
    "Z3_2_symbreak": {4, 6, 8, 10, 12},
    "smt_Z3":  {4, 6, 8, 10},
    "smt_Z3_symbreak":  {4, 6, 8, 10},
    "smt_Z3_optimize":  {4, 6, 8, 10},
    "smt_Z3_optimize_symbreak":  {4, 6, 8, 10},
    "basic_gecode": {4, 6, 8, 10, 12},
    "local_symbreak_gecode": {4, 6, 8, 10, 12, 14},
    "local_noimplied_gecode": {4, 6, 8, 10, 12, 14},
    "global_symbreak_gecode": {4, 6, 8, 10, 12},
    "global_symbreak_opt_gecode": {4, 6, 8, 10},
    "basic_chuffed": {4, 6, 8, 10},
    "local_symbreak_chuffed": {4, 6, 8, 10, 12, 14},
    "local_noimplied_chuffed": {4, 6, 8, 10, 12, 14},
    "global_symbreak_chuffed": {4, 6, 8, 10, 12, 14},
    "global_symbreak_opt_chuffed": {4, 6, 8, 10, 12},
    "base_cbc": {4, 6, 8, 10, 12},
    "base_opt_cbc": {4, 6, 8, 10, 12},
    "symbreak_cbc": {4, 6, 8, 10, 12},
    "symbreak_opt_cbc": {4, 6, 8, 10, 12},
    "base_highs": {4, 6, 8, 10, 12},
    "base_opt_highs": {4, 6, 8, 10, 12},
    "symbreak_highs": {4, 6, 8, 10, 12},
    "symbreak_opt_highs": {4, 6, 8, 10, 12},
}

paradigms = {
    "Z3_1": "SAT",
    "Z3_1_symbreak": "SAT",
    "MINISAT22_1": "SAT",
    "MINISAT22_1_symbreak": "SAT",
    "GLUCOSE3_1": "SAT",
    "GLUCOSE3_1_symbreak": "SAT",
    "Z3_2": "SAT",
    "Z3_2_symbreak": "SAT",
    "smt_Z3":  "SMT",
    "smt_Z3_symbreak":  "SMT",
    "smt_Z3_optimize":  "SMT",
    "smt_Z3_optimize_symbreak": "SMT",
    "basic_gecode": "CP",
    "local_symbreak_gecode": "CP",
    "local_noimplied_gecode": "CP",
    "global_symbreak_gecode": "CP",
    "global_symbreak_opt_gecode": "CP",
    "basic_chuffed": "CP",
    "local_symbreak_chuffed": "CP",
    "local_noimplied_chuffed": "CP",
    "global_symbreak_chuffed": "CP",
    "global_symbreak_opt_chuffed": "CP",
    "base_cbc": "MIP",
    "base_opt_cbc": "MIP",
    "symbreak_cbc": "MIP",
    "symbreak_opt_cbc": "MIP",
    "base_highs": "MIP",
    "base_opt_highs": "MIP",
    "symbreak_highs": "MIP",
    "symbreak_opt_highs": "MIP",
}

def matrix_style_json(obj, indent=2):
    """
    Convert any nested dict/list structure to JSON string
    where list-of-lists are kept in matrix-style format.
    """
    def serialize(obj, level=0):
        spacing = ' ' * (level * indent)
        
        if isinstance(obj, dict):
            items = []
            for k, v in obj.items():
                items.append(f'{spacing}"{k}": {serialize(v, level + 1)}')
            return '{\n' + ',\n'.join(items) + f'\n{spacing}}}'
        
        elif isinstance(obj, list):
            # Check if this is a list-of-lists (all elements are lists)
            if all(isinstance(i, list) for i in obj) and obj:
                # Keep each sublist on one line
                inner_items = [json.dumps(sublist) for sublist in obj]
                inner_spacing = ' ' * ((level + 1) * indent)
                return '[\n' + inner_spacing + (',\n' + inner_spacing).join(inner_items) + f'\n{spacing}]'
            else:
                # For regular lists, use compact JSON
                return json.dumps(obj)
        
        else:
            # For primitives: int, float, bool, str
            return json.dumps(obj)
    
    return serialize(obj)


def save_results(solver, n, results):
  paradigm = paradigms[solver]
  main_folder = Path(__file__).resolve().parent.parent #main folder is up two levels from this script
  res_dir = main_folder / "res" / paradigm.upper()
  res_dir.mkdir(parents=True, exist_ok=True)

  file_name = f"{n}.json"
  file_path = res_dir / file_name

  if file_path.exists():
    with open(file_path, "r") as f:
      existent_file = json.load(f)
  else:
    existent_file = {}
  
  existent_file[solver] = results

  with open(file_path, "w") as f:
     #json.dump(existent_file, f, indent=2, separators=(",", ":"))
     f.write(matrix_style_json(existent_file))
  
  print(f"Results saved to {file_path}.")

# Solve all the instances together
def run_all_solvers_all_teams():
    for solver_key, solver_func in SOLVERS.items():
        valid_teams = VALID_TEAMS.get(solver_key, set())
        for num_teams in valid_teams:
            print(f"\nRunning model '{solver_key}' with {num_teams} teams...")
            results = solver_func(num_teams)
            save_results(solver_key, num_teams, results)

if __name__ == "__main__":
    run_all_solvers_all_teams()