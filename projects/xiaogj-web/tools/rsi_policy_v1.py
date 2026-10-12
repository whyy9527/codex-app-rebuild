"""Revision from actual replay: honor zero effort and stop at verified quality 1.

Only the revealed prefix is consumed; no source dataset or future tree is read.
The fixed score is a fraction, so 1 means all requirements in this protocol,
not completion of the rebuild product.
"""
def select(view, rho):
    if rho == 0 or view['round'] >= max(1, int(4 * rho)):
        return []
    if any(node['score'] >= 1 for node in view['nodes']):
        return []
    eligible = [node for node in view['nodes'] if node['id'] in view['eligible']]
    best = max(eligible, key=lambda node: (node['score'], node['seq']))
    return [best['id']]
