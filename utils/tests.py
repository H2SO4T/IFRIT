import pandas
import numpy as np
from functools import reduce
from operator import mul
from fractions import Fraction
from math import sqrt


def nCk(n, k):
    return int(reduce(mul, (Fraction(n - i, i + 1) for i in range(k)), 1))


def uniform_comparison(ori_dist, eps2=0.1):
    if not ori_dist:
        print("Empty")
        return
    dist = pandas.DataFrame(ori_dist)
    domain = np.unique(dist, axis=0)
    # The numer of samples come from lemma 5 of collision-based testers are optimal for uniformity and closeness
    expected = 6 * sqrt(len(domain)) / eps2
    if len(ori_dist) < expected:
        print("You need " + str(expected) + " samples")
    else:
        print("The domain lenght is: " + str(len(domain)))
    s = 0
    for i in range(len(ori_dist)):
        s = s + ori_dist[(i + 1):len(ori_dist)].count(ori_dist[i])
    t = nCk(len(ori_dist), 2) * (1 + 3 / 4 * eps2) / len(domain)
    if s > t:
        return False
    else:
        return True


# function that computes the diversity of a list of strings
def diversity_strings(list_of_strings):
    list_of_strings = [str(x) for x in list_of_strings]
    return len(set(list_of_strings))/len(list_of_strings)
