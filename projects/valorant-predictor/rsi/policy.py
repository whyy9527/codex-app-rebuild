def select(view, rho):
    if view['round'] >= 8:
        return []
    return [max((n for n in view['nodes'] if n['id'] in view['eligible']), key=lambda n: (n['score'], n['seq']))['id']]
