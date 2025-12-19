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
var int: totDistance;

% Every team play once a week
constraint forall(j in WEEK)(global_cardinality([tHome[i,j]| i in PERIOD] ++ [tAway[i,j]|i in PERIOD], TEAMS,[1 | t in TEAMS]));

% Each team plays at most twice in the same period
constraint forall(i in PERIOD) (global_cardinality([tHome[i,j]|j in WEEK] ++ [tAway[i,j]| j in WEEK],TEAMS,[0 | t in TEAMS], [2 | t in TEAMS]));

% Each pair plays once
constraint forall(t1,t2 in TEAMS where t1 < t2)(sum(i in PERIOD,j in WEEK)(tHome[i,j] = t1 /\ tAway[i,j] = t2) + sum(i in PERIOD,j in WEEK)(tHome[i,j] = t2 /\ tAway[i,j] = t1) = 1);



% Each team cannot play against itself
constraint forall(i in PERIOD, j in WEEK)(tHome[i,j] != tAway[i,j]);


% Implied: each team plays exactly n-1 times
constraint global_cardinality([tHome[i,j]|i in PERIOD,j in WEEK]++[tAway[i,j]|i in PERIOD, j in WEEK], TEAMS, [n-1 | t in TEAMS]);


% Symmetry break: fix first week
constraint forall(i in PERIOD)(tHome[i, 1] = i /\ tAway[i, 1] = i + periods);

% Symmetry break: lexicographically order home teams by week
function array[int] of var int: getcol(array[int,int] of var int: M,int: j) =[M[i, j]|i in PERIOD];

constraint forall(j in 2..weeks-1) (lex_lesseq(getcol(tHome,j), getcol(tHome,j+1)));


constraint totDistance = sum(t in TEAMS)(abs(sum(i in PERIOD, j in WEEK)(tHome[i,j]=t) - sum(i in PERIOD, j in WEEK)(tAway[i,j]=t)));

%% Gecode search strategy
%solve :: int_search([tHome[i,j]|i in PERIOD,j in WEEK]++[tAway[i,j]|i in PERIOD, j in WEEK], dom_w_deg, indomain_random)::restart_luby(250) minimize totDistance;

%% Chuffed search strategy
solve :: restart_geometric(1.5, 100) minimize totDistance;

