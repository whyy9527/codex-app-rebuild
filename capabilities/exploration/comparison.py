"""Paired online conditions and separate quality/call statistics; no synthetic gain claims."""
from capabilities.exploration.ledger import digest


def compare_runs(fixed, updated):
    for key in ('input_digest','max_calls','width'):
        if fixed['config'][key] != updated['config'][key]:
            raise ValueError('comparison condition differs: '+key)
    all_nodes = fixed['nodes'] + updated['nodes']
    protocols = {node['observation'].get('protocol_digest') for node in all_nodes}
    generators = {node['generation'].get('generator_protocol') for node in all_nodes if node['generation']}
    if len(protocols)!=1 or None in protocols or len(generators)!=1 or None in generators:
        raise ValueError('evaluation or generator protocol differs')
    attestations = [node['generation'].get('attestation') for node in all_nodes if node['generation']]
    verified = bool(attestations) and all(isinstance(a,dict) for a in attestations)
    if verified and len({digest(a) for a in attestations}) != 1:
        raise ValueError('runtime model attestation differs')
    result = {'control_status':'verified_model_protocol' if verified else 'partial_model_unattested',
              'protocol_digest':next(iter(protocols)), 'generator_protocol':next(iter(generators)),
              'model_cost':None, 'interpretation':'observed pair only; not statistical replication'}
    for name, run in [('fixed',fixed),('updated',updated)]:
        result[name] = {'generation_calls':len(run['nodes']),
                        'best_score':max((node['score'] for node in run['nodes']),default=0),
                        'failed_attempts':sum(node['score']==0 for node in run['nodes'])}
    return result
