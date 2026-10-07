"""Model-driven code revision from frozen replay feedback, independent of any template portfolio."""
import ast
import hashlib
import re
from capabilities.exploration.ledger import canonical, digest
from capabilities.exploration.objective import select_policy
from runtime.policy_runtime import RestrictedPolicy, validate_source
from capabilities.exploration.pool import select_pool


def shape(source):
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant):
            node.value = 0
    return ast.dump(tree, include_attributes=False)


def develop_policy(worker, worlds, current_source, *, previous_feedback=None, width=2,
                   max_calls=6, max_rounds=6, penalty=.05, candidate_sources=()):
    incumbent = RestrictedPolicy(current_source)
    baseline = select_policy(worlds, {'incumbent': incumbent}, incumbent='incumbent', width=width,
                             max_calls=max_calls, max_rounds=max_rounds, penalty=penalty, semantics='paper')
    if candidate_sources:
        baseline=select_pool(worlds,current_source,candidate_sources,width=width,max_calls=max_calls,
                             max_rounds=max_rounds,penalty=penalty)
    feedback = {'current_replay': baseline, 'previous_feedback': previous_feedback,
                'completed_worlds': worlds, 'current_source': current_source}
    prompt = ('You are the policy-development agent in a Dream-RSI experiment. Revise executable Python '
              'policy(observed, context) based on the frozen replay feedback below. Propose new code, not a template name. '
              'The deployed policy sees ONLY observed nodes and public context: width, remaining_calls, remaining_rounds, '
              'rho, legal_parents. Return a list of unique legal parent IDs, at most width and remaining_calls; [] stops. '
              'Root opens the earliest unseen branch; leaves refine. Never hardcode historical node IDs, hidden scores, '
              'future outcomes, or worlds into the policy. The developer can inspect completed history, the deployed policy cannot. '
              'Use functions and literal constants only; no imports, globals, default parameters, decorators, filesystem or tools. '
              'Restricted builtins include len,min,max,sum,sorted,range,enumerate,zip,list,dict,set,tuple,int,float,str,bool,abs,round,all,any,next. '
              'Dict get/items/keys/values, list append/sort and math ceil/floor/sqrt/log/isfinite are available. '
              'Recorded observations may contain receipts; use actual score fields for quality. Explain the causal failure '
              'and intended strategy change in rationale. Do not use tools. Feedback: ' + canonical(feedback))
    reply = worker.generate(prompt, role='policy-development')
    source = reply['source']
    result = {'source': source, 'rationale': reply['rationale'], 'model_receipt': reply['receipt'],
              'feedback_digest': digest(feedback), 'previous_feedback_digest': digest(previous_feedback),
              'incumbent_source_digest': hashlib.sha256(current_source.encode()).hexdigest(),
              'source_changed': source != current_source, 'structure_changed': None,
              'selected': baseline['selected'], 'selected_source':baseline.get('selected_source',current_source)}
    try:
        tree = validate_source(source)
        result['structure_changed'] = shape(source) != shape(current_source)
        if any(isinstance(node, ast.Constant) and isinstance(node.value, str)
               and re.fullmatch(r'n\d{4,}', node.value) for node in ast.walk(tree)):
            raise ValueError('hardcoded historical node identifier')
        proposal = RestrictedPolicy(source)
        selection = select_policy(worlds, {'incumbent': incumbent, 'proposal': proposal},
                                  incumbent='incumbent', width=width, max_calls=max_calls,
                                  max_rounds=max_rounds, penalty=penalty, semantics='paper')
        if candidate_sources:
            selection=select_pool(worlds,current_source,candidate_sources,proposal_source=source,
                                  width=width,max_calls=max_calls,max_rounds=max_rounds,penalty=penalty)
        result.update(status='evaluated', selection=selection, selected=selection['selected'],
                      selected_source=selection.get('selected_source',source if selection['selected']=='proposal' else current_source))
    except (ValueError, SyntaxError) as error:
        result.update(status='rejected', rejection=str(error), selection=baseline)
    return result
