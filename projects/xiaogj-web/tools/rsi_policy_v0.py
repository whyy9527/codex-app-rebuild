"""Initial finite policy: continue two levels, then sample another root branch."""
def select(view, rho):
    if view['round'] >= max(1, int(4 * rho)):
        return []
    if view['round'] in (0, 3):
        return [view['nodes'][0]['id']]
    return [view['eligible'][-1]]
