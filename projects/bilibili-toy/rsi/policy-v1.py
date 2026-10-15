"""Revision after v0 repeated its first branch on the third call.

Continue the strongest revealed leaf rather than restarting discovery. Budget
two online probes per deployment to leave an explicit inspection boundary;
this is execution batching, not a completeness threshold.
"""
def select(view, rho):
    if rho == 0 or view['round'] >= max(1, round(2 * rho)):
        return []
    eligible = [n for n in view['nodes'] if n['id'] in view['eligible']]
    return [max(eligible, key=lambda n: (n['score'], n['seq']))['id']]
