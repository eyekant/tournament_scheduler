include "globals.mzn";

% Instance parameters
int: n; % Number of teams (must be even)

constraint assert(n mod 2 == 0, "Input error: n must be even.");

% Domains
set of int: TEAMS = 1..n;

% Decision variables
int: periods = n div 2;
set of int: PERIOD = 1..periods;
int: weeks = n-1;
set of int: WEEK = 1..weeks;
array[PERIOD, WEEK] of var TEAMS: tHome;
array[PERIOD, WEEK] of var TEAMS: tAway;


% Every team play once a week
constraint forall(j in WEEK)(global_cardinality([tHome[i,j]| i in PERIOD] ++ [tAway[i,j]|i in PERIOD], TEAMS,[1 | t in TEAMS]));

% Each team plays at most twice in the same period
constraint forall(i in PERIOD)(global_cardinality([tHome[i,j]|j in WEEK] ++ [tAway[i,j]| j in WEEK],TEAMS,[0 | t in TEAMS], [2 | t in TEAMS]));

% Each pair plays once
constraint forall(t1,t2 in TEAMS where t1 < t2)(sum(i in PERIOD,j in WEEK)(tHome[i,j] = t1 /\ tAway[i,j] = t2) + sum(i in PERIOD,j in WEEK)(tHome[i,j] = t2 /\ tAway[i,j] = t1) = 1);



% Symmetry break: lex order home index less than away
constraint forall(i in PERIOD, j in WEEK)(tHome[i,j] < tAway[i,j]);

% Symmetry break: fix first week
constraint forall(i in PERIOD) (tHome[i, 1] = i /\ tAway[i, 1] = i + periods);



% Implied: each team plays exactly n-1 times
constraint global_cardinality([tHome[i,j]|i in PERIOD,j in WEEK]++[tAway[i,j]|i in PERIOD, j in WEEK], TEAMS, [n-1 | t in TEAMS]);



%% Gecode search strategy
% solve :: int_search([tHome[i,j]|i in PERIOD,j in WEEK]++[tAway[i,j]|i in PERIOD, j in WEEK], dom_w_deg, indomain_random)::restart_luby(250) satisfy;

%% Chuffed search strategy
solve :: int_search([tHome[i,j]|i in PERIOD,j in WEEK]++[tAway[i,j]|i in PERIOD, j in WEEK], first_fail, indomain_min)::restart_geometric(2.0, 50) satisfy;
