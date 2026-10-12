"""Revision from live pagination replay: avoid retrying an exhausted probe set.

Quality may remain below one because a source hypothesis fails. Stop after all
three fixed protocol probes have independent receipts; preserve that failure.
Only the revealed prefix is read. This is not a product completion condition.
"""
def select(view, rho):
    if rho == 0 or view['round'] >= max(1, int(4 * rho)):
        return []

    def coverage(node):
        return len(node.get('observation', {}).get('evaluation', {}).get('checks', []))

    if any(coverage(node) == 3 for node in view['nodes']):
        return []
    eligible = [node for node in view['nodes'] if node['id'] in view['eligible']]
    best = max(eligible, key=lambda node: (coverage(node), node['score'], node['seq']))
    return [best['id']]
