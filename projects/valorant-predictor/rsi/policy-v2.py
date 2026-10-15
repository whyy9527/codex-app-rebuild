"""After real feedback: spend rho's budget, stop after unavailable source action."""
def select(view, rho):
    if view['round'] >= max(1, round(8 * rho)):
        return []
    eligible = [n for n in view['nodes'] if n['id'] in view['eligible']]
    best = max(eligible, key=lambda n: (n['score'], n['seq']))
    evaluation = best['observation'].get('evaluation', {})
    if evaluation.get('error') or (evaluation and not evaluation.get('remaining')):
        return []
    return [best['id']]
