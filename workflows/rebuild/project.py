"""Read one rebuild project; prepare a native Goal or call its existing commands.

No task state, hooks, model process or implicit Goal creation lives here.
All project paths are relative to the explicitly selected workspace.
"""
import argparse
from collections import Counter
import json
from pathlib import Path
import re
from string import Template
import subprocess
import sys

from capabilities.exploration.storage import digest
from capabilities.rebuild.contracts import local_file, require_text
from capabilities.rebuild.discovery import frontier
from runtime.dream import load_pool


def load_project(workspace, name):
    root = Path(workspace).resolve()
    project = json.loads(local_file(root, name).read_text())
    if not isinstance(project, dict):
        raise ValueError('project must be a JSON object')
    if type(project.get('schema_version')) is not int or project['schema_version'] != 1:
        raise ValueError('project schema_version 1 required')
    for field in ('name', 'source', 'target', 'objective'):
        require_text(project.get(field), 'project.' + field)
    completion = project.get('completion')
    if not isinstance(completion, list) or not completion:
        raise ValueError('project completion criteria required')
    for item in completion:
        require_text(item, 'completion criterion')
    inputs = project.get('inputs', {})
    if not isinstance(inputs, dict):
        raise ValueError('project.inputs must map names to existing workspace files')
    for path in inputs.values():
        local_file(root, path)
    commands = project.get('commands', {})
    if not isinstance(commands, dict):
        raise ValueError('project.commands must map names to argv lists')
    for key, argv in commands.items():
        require_text(key, 'command name')
        if not isinstance(argv, list) or not argv:
            raise ValueError('project command must be a nonempty argv list')
        for argument in argv:
            require_text(argument, 'command argument')
    return root, project


def goal_payload(project, name, workspace):
    workflow = Path(__file__).resolve().with_name('WORKFLOW.md')
    template = workflow.with_name('GOAL.template.md').read_text()
    values = {key: project[key] for key in ('name', 'source', 'target', 'objective')}
    values.update(workspace=str(workspace), project=str(workspace / name),
                  workflow=str(workflow), research=str(workflow.parents[2] / 'docs/RESEARCH.md'),
                  completion='\n'.join(
        f'{index}. {text}' for index, text in enumerate(project['completion'], 1)))
    # Values are substituted once, so dollar signs in user content remain literal.
    return {'objective': Template(template).substitute(values).strip()}


def project_status(root, project):
    inputs = project.get('inputs', {})
    read = lambda key: json.loads(local_file(root, inputs[key]).read_text())
    result = {'name': project['name'], 'commands': sorted(project.get('commands', {})),
              'completion': 'not evaluated; this is an evidence index, not a Goal verifier'}
    contract = None
    if 'frontend_contract' in inputs:
        contract = read('frontend_contract')
        result['mold'] = {'path': inputs['frontend_contract'],
                          'requirements': len(contract['requirements']),
                          'by_kind': dict(Counter(row['kind'] for row in contract['requirements']))}
    if 'exploration_history' in inputs:
        history = read('exploration_history')
        pending = frontier(root, history)
        result['exploration'] = {'states': len(history['states']),
                                 'transitions': len(history['transitions']),
                                 'pending_probes': len(pending['pending']),
                                 'completion': pending['completion']}
    if 'rsi_pool' in inputs:
        pool, worlds, _ = load_pool(root, inputs['rsi_pool'])
        result['rsi'] = {'worlds': len(worlds), 'nodes': [len(w['nodes']) for w in worlds],
                         'policy': pool['policy'], 'protocol': pool['protocol'],
                         'completion': 'not evaluated; replay score is not product acceptance'}
    if 'historical_frontend_result' in inputs:
        receipt = read('historical_frontend_result')
        result['historical_frontend'] = {
            'path': inputs['historical_frontend_result'], 'status': receipt['status'],
            'counts': dict(Counter(row['status'] for row in receipt['rows'])),
            'contract_matches': contract is not None and receipt.get('contract_digest') == digest(contract),
            'freshness': 'historical only; current source and binary have not been verified by this command'}
    return result


def command_argv(root, project, command, *, out=None, observed=None):
    if command not in project.get('commands', {}):
        raise ValueError('unknown project command: ' + command)
    values = {}
    if out is not None:
        target = local_file(root, out, must_exist=False)
        if target.exists():
            raise ValueError('choose a fresh output path; existing evidence is preserved')
        values['out'] = out
    if observed is not None:
        local_file(root, observed)
        values['observed'] = observed
    def substitute(match):
        key = match.group(1)
        if key not in values:
            raise ValueError('command requires --' + key)
        return values[key]
    return [re.sub(r'\{(out|observed)\}', substitute, argument)
            for argument in project['commands'][command]]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('operation', choices=('goal', 'status', 'run'))
    parser.add_argument('--workspace', required=True)
    parser.add_argument('--project', required=True)
    parser.add_argument('--command')
    parser.add_argument('--out')
    parser.add_argument('--observed')
    parser.add_argument('--dry-run', action='store_true')
    args = parser.parse_args()
    try:
        root, project = load_project(args.workspace, args.project)
        if args.operation == 'goal':
            result = goal_payload(project, args.project, root)
        elif args.operation == 'status':
            result = project_status(root, project)
        else:
            if not args.command:
                raise ValueError('run requires --command')
            argv = command_argv(root, project, args.command, out=args.out, observed=args.observed)
            if not args.dry_run:
                # Trusted local argv; preserve the actual command's exit code.
                return subprocess.run(argv, cwd=root).returncode
            result = {'argv': argv, 'executed': False}
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except (ValueError, OSError, KeyError, TypeError) as error:
        print(json.dumps({'status': 'invalid', 'error': str(error)}, ensure_ascii=False), file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
