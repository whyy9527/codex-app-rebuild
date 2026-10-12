"""Revision from grade replay: retain zero-effort choice and stop at quality 1.
The initial policy repeats completed work and reopens a partial root branch.
Only revealed scores and eligible nodes are used; no frozen future is read.
"""
def select(view, rho):
    if rho == 0 or view['round'] >= max(1, int(4 * rho)):
        return []
    if any(node['score'] >= 1 for node in view['nodes']):
        return []
    eligible = [node for node in view['nodes'] if node['id'] in view['eligible']]
    return [max(eligible, key=lambda node: (node['score'], node['seq']))['id']]
