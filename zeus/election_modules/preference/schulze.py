import json
import sys

MIN_INT = -sys.maxsize

def create_preferences_array(n_candidates, ballots):

    prefs = [ [ 0 for c in range(n_candidates) ] for r in range(n_candidates) ]
    for ballot in ballots:
        for i, first_candidate in enumerate(ballot):
            for second_candidate in ballot[i:]:
                prefs[first_candidate][second_candidate] += 1

    return prefs

def calc_strongest_paths(preferences):

    n = len(preferences)

    strengths = [ [ 0 for c in range(n) ] for r in range(n) ]

    for i in range(n):
        for j in range(n):
            if preferences[i][j] > preferences[j][i]:
                strengths[i][j] = preferences[i][j] - preferences[j][i]
            else:
                strengths[i][j] = MIN_INT


    for k in range(n):
        for i in range(n):
            if i != k:
                for j in range(n):
                    if j != i:
                        min_strength = min(strengths[i][k], strengths[k][j])
                        if strengths[i][j] < min_strength:
                            strengths[i][j] = min_strength

    return strengths


def calc_results(strengths):

    n = len(strengths)

    wins = []
    for i in range(n):
        beaten_candidates = []
        for j in range(n):
            if i != j:
                if strengths[i][j] > strengths[j][i]:
                    beaten_candidates.append(j)
        wins.append(beaten_candidates)

    return wins

def print_results(wins, candidates):
    for i, beaten_candidates in enumerate(wins):
        beaten_candidates_names = [ candidates[cnd]
                                    for cnd in beaten_candidates ]
        n_wins = len(beaten_candidates)
        print(candidates[i], '=', n_wins, beaten_candidates_names)


def count(ballots, candidates):
    preferences = create_preferences_array(len(candidates), ballots)
    strengths = calc_strongest_paths(preferences)
    wins = calc_results(strengths)
    beats = {}
    for i, beaten_candidates in enumerate(wins):
        n_wins = len(beaten_candidates)
        beats[candidates[i]] = (n_wins, beaten_candidates)

    return wins, beats


if __name__ == "__main__":

    with open(sys.argv[1]) as input_file:
        election = json.load(input_file)

    candidates = election['candidates']
    ballots = election['ballots']

    preferences = create_preferences_array(len(candidates), ballots)
    strengths = calc_strongest_paths(preferences)
    wins = calc_results(strengths)
    print_results(wins, candidates)
