% The action rules are ordered by priority

:- dynamic position/4.
:- dynamic wields_weapon/2.
:- dynamic health/1.
:- dynamic has/3.
:- dynamic stepping_on/3.
:- dynamic unsafe_position/2.

%%% RULES FOR ACTION SELECTION %%%
% R and C stands for Row and Column, to indicate the coordinate of the entities.
% For movement actions, always check is the direction selected is safe.

% eat the apple and win the game
action(eat) :- has(agent, comestible, apple).

%%% "Deal with enemies" rules %%%
% These 3 rules are mutually exclusive

% attack an enemy
% the attack is automatic when you move towards it
% in this case, it is useless to check if the new position is safe - it is already occupied by the enemy
action(attack(Direction)) :- position(agent, _, AgentR, AgentC), position(enemy, Type, EnemyR, EnemyC),
                             wields_weapon(agent, Weapon), is_beatable(Type, Weapon),
                             is_close(AgentR, AgentC, EnemyR, EnemyC), healthy,
                             next_step(AgentR, AgentC, EnemyR, EnemyC, Direction).

% run away from an enemy, when it is not safe to attack
% choose the opposite direction wrt the enemy position
action(run(OppositeDirection)) :- position(agent, _, AgentR, AgentC), position(enemy, _, EnemyR, EnemyC),
                                  is_close(AgentR, AgentC, EnemyR, EnemyC), \+ healthy,
                                  next_step(AgentR, AgentC, EnemyR, EnemyC, Direction),
                                  opposite(Direction, OD), safe_direction(AgentR, AgentC, OD, OppositeDirection).

% if not wielded, go towards the weapon available in the map
action(get_to_weapon(Direction)) :- position(agent, _, AgentR, AgentC), position(enemy, Type, EnemyR, EnemyC),
                                    is_close(AgentR, AgentC, EnemyR, EnemyC),
                                    wields_weapon(agent, Weapon), \+ is_beatable(Type, Weapon),
                                    position(weapon, tsurugi, WeaponR, WeaponC),
                                    next_step(AgentR, AgentC, WeaponR, WeaponC, D), safe_direction(AgentR, AgentC, D, Direction).

%%% End of "Deal with enemies" rules %%%

%%% "Deal with objects" rules %%%

% pick up an object
action(pick) :- stepping_on(agent, ObjClass, _), is_pickable(ObjClass).

% if the agent has a weapon, wield it
action(wield(Weapon)) :- has(agent, weapon, Weapon).

%%% End of "Deal with objects" rules %%%

% If you cannot apply previous rules, just go towards the goal
% get the next movement to get closer to the goal
action(move(Direction)) :- position(agent, _, AgentR, AgentC), position(comestible, apple, AppleR, AppleC),
                           next_step(AgentR, AgentC, AppleR, AppleC, D), safe_direction(AgentR, AgentC, D, Direction).

% If the apple is not visible on the map - e.g. the enemy took it
% Try to kill it, if beatable
action(move_towards_enemy(Direction)) :- \+ position(comestible, apple, _, _), position(agent, _, AgentR, AgentC),
                                       position(enemy, Type, EnemyR, EnemyC), wields_weapon(agent, Weapon),
                                       is_beatable(Type, Weapon), next_step(AgentR, AgentC, EnemyR, EnemyC, D),
                                       safe_direction(AgentR, AgentC, D, Direction).

% If not beatable, go towards the weapon
action(get_to_weapon(Direction)) :- \+ position(comestible, apple, _, _), position(agent, _, AgentR, AgentC),
                                       position(enemy, Type, _, _), wields_weapon(agent, Weapon),
                                       \+ is_beatable(Type, Weapon), position(weapon, tsurugi, WeaponR, WeaponC),
                                       next_step(AgentR, AgentC, WeaponR, WeaponC, D), safe_direction(AgentR, AgentC, D, Direction).

%%% END OF RULES FOR ACTION SELECTION %%%

% test the different condition for closeness
% two objects are close if they are at 1 cell distance, including diagonals
is_close(R1,C1,R2,C2) :- R1 == R2, (C1 is C2+1; C1 is C2-1).
is_close(R1,C1,R2,C2) :- C1 == C2, (R1 is R2+1; R1 is R2-1).
is_close(R1,C1,R2,C2) :- (R1 is R2+1; R1 is R2-1), (C1 is C2+1; C1 is C2-1).

% the agent can perform "dangerous" actions - e.g. attack a monster - if its health is above 50%
healthy :- health(H), H > 50.

% compute the direction given the starting point and the target position
% check if the direction leads to a safe position
% D = temporary direction - may be unsafe
% Direction = the definitive direction 
next_step(R1,C1,R2,C2, D) :-
    ( R1 == R2 -> ( C1 > C2 -> D = west; D = east );
    ( C1 == C2 -> ( R1 > R2 -> D = north; D = south);
    ( R1 > R2 ->
        ( C1 > C2 -> D = northwest; D = northeast );
        ( C1 > C2 -> D = southwest; D = southeast )
    ))).
    % safe_direction(R1, C1, D, Direction).

% check if the selected direction is safe
safe_direction(R, C, D, Direction) :- resulting_position(R, C, NewR, NewC, D),
                                      ( safe_position(NewR, NewC) -> Direction = D;
                                      % else, get a new close direction
                                      % and check its safety
                                      close_direction(D, ND), safe_direction(R, C, ND, Direction)
                                      ).

% a square if unsafe if there is a trap or an enemy
unsafe_position(R, C) :- position(trap, _, R, C).
unsafe_position(R, C) :- position(enemy, _, R, C).
unsafe_position(R,C) :- position(enemy, _, ER, EC), is_close(ER, EC, R, C).



%%%% known facts %%%%
opposite(north, south).
opposite(south, north).
opposite(east, west).
opposite(west, east).
opposite(northeast, southwest).
opposite(southwest, northeast).
opposite(northwest, southeast).
opposite(southeast, northwest).

resulting_position(R, C, NewR, NewC, north) :-
    NewR is R-1, NewC = C.
resulting_position(R, C, NewR, NewC, south) :-
    NewR is R+1, NewC = C.
resulting_position(R, C, NewR, NewC, west) :-
    NewR = R, NewC is C-1.
resulting_position(R, C, NewR, NewC, east) :-
    NewR = R, NewC is C+1.
resulting_position(R, C, NewR, NewC, northeast) :-
    NewR is R-1, NewC is C+1.
resulting_position(R, C, NewR, NewC, northwest) :-
    NewR is R-1, NewC is C-1.
resulting_position(R, C, NewR, NewC, southeast) :-
    NewR is R+1, NewC is C+1.
resulting_position(R, C, NewR, NewC, southwest) :-
    NewR is R+1, NewC is C-1.

close_direction(north, northeast).
close_direction(northeast, east).
close_direction(east, southeast).
close_direction(southeast, south).
close_direction(south, southwest).
close_direction(southwest, west).
close_direction(west, northwest).
close_direction(northwest, north).

has(agent, _, _) :- fail.

unsafe_position(_,_) :- fail.
safe_position(R,C) :- \+ unsafe_position(R,C).

is_beatable(kobold, _).
is_beatable(giantmummy, tsurugi).

is_pickable(comestible).
is_pickable(weapon).