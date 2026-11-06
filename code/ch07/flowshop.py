"""Chapter 7: permutation flow shop basics: data, makespan, Johnson."""
import itertools
import random


# [start:taillard]
def taillard_instance(seed: int, n: int, m: int) -> list[list[int]]:
    """Taillard's (1993) generator: p[i][j] for machine i, job j.

    A Lehmer random number generator.  With the published seeds it
    reproduces the benchmark instances exactly (ta001 uses seed
    873654221 with n=20 jobs and m=5 machines).
    """
    a, b, c, mod = 16807, 127773, 2836, 2**31 - 1
    p = [[0] * n for _ in range(m)]
    for i in range(m):
        for j in range(n):
            k = seed // b
            seed = a * (seed % b) - k * c
            if seed < 0:
                seed += mod
            p[i][j] = 1 + int(seed / mod * 99)
    return p
# [end:taillard]


# [start:makespan]
def makespan(p: list[list[int]], order: list[int]) -> int:
    """C[i] = completion time of the latest job on machine i.

    A job starts on machine i when it has left machine i-1 *and*
    machine i has finished the previous job.
    """
    m = len(p)
    C = [0] * m
    for j in order:
        C[0] += p[0][j]
        for i in range(1, m):
            C[i] = max(C[i], C[i - 1]) + p[i][j]
    return C[-1]
# [end:makespan]


# [start:johnson]
def johnson(p: list[list[int]]) -> list[int]:
    """Johnson's rule, optimal for F2 || Cmax.

    Jobs faster on machine 1 than on machine 2 go first, by increasing
    time on machine 1.  The others go last, by decreasing time on
    machine 2.
    """
    n = len(p[0])
    first = sorted((j for j in range(n) if p[0][j] < p[1][j]),
                   key=lambda j: p[0][j])
    last = sorted((j for j in range(n) if p[0][j] >= p[1][j]),
                  key=lambda j: -p[1][j])
    return first + last
# [end:johnson]


if __name__ == "__main__":
    # [start:check]
    p = taillard_instance(873654221, 20, 5)
    print("ta001, machine 1, jobs 1-10:", p[0][:10])
    rng = random.Random(1)
    for _ in range(100):
        n = rng.randint(2, 7)
        q = [[rng.randint(1, 20) for _ in range(n)] for _ in range(2)]
        best = min(makespan(q, list(o))
                   for o in itertools.permutations(range(n)))
        assert makespan(q, johnson(q)) == best
    print("Johnson's rule matched brute force on 100 F2 instances")
    # [end:check]
