"""Spend the frozen four-journey horizon proportionally; stop after complete/error."""
def select(view,rho):
    if view['round']>=max(1,round(4*rho)):
        return []
    eligible=[n for n in view['nodes']if n['id']in view['eligible']]
    best=max(eligible,key=lambda n:(n['score'],n['seq']))
    observation=best['observation'].get('evaluation',{})
    if observation.get('error')or(observation and not observation.get('remaining')):
        return []
    return [best['id']]
