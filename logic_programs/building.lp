width(3).
depth(3).
height(3).
cell(X,Y,Z) :-
  X=0..(W-1), width(W),
  Y=0..(D-1), depth(D),
  Z=0..(H-1), height(H).

7 {build(X,Y,Z): cell(X,Y,Z)} 7.
build(N) :- build(X,Y,Z), N = X * 9 + Y * 3 + Z.

:- build(X,Y,Z), Z > 0, not build(X, Y, Z-1).

:- build(X,Y,Z),
  not build(X-1, Y, Z), not build(X+1, Y, Z),
  not build(X, Y-1, Z), not build(X, Y+1, Z),
  not build(X, Y, Z+1), not build(X, Y, Z+1).

basesUsed(B) :- B = #count{X,Y: build(X,Y,0)}.

#minimize {B: basesUsed(B)}.

#show build/1.