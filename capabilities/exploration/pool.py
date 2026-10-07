"""Re-evaluate the complete source pool on all completed worlds."""
import hashlib
from capabilities.exploration.objective import select_policy
from runtime.policy_runtime import RestrictedPolicy


def select_pool(worlds, incumbent_source, sources, **settings):
    candidates={'incumbent':RestrictedPolicy(incumbent_source)}
    source_by_name={'incumbent':incumbent_source}
    for source in sources:
        if source==incumbent_source: continue
        name='archive-'+hashlib.sha256(source.encode()).hexdigest()
        candidates[name]=RestrictedPolicy(source)
        source_by_name[name]=source
    result=select_policy(worlds,candidates,incumbent='incumbent',semantics='paper',**settings)
    result['selected_source']=source_by_name[result['selected']]
    return result
