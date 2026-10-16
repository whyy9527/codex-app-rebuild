"""Opening exploration: alternate independent root probes and continuation."""
def select(view, rho):
    if view['round'] >= max(1, int(3 * rho)):
        return []
    if view['round'] % 2 == 0:
        return [view['nodes'][0]['id']]
    return [view['eligible'][-1]]
