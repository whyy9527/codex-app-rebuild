"""Short Codex lifecycle adapter. No model calls and no verifier execution in hooks."""
import argparse
import json
from pathlib import Path
import sys
import time
from capabilities.exploration.harness import Harness
from runtime.harness_mcp import summary

GUIDANCE=('Exploration Lab MCP tools support explicitly requested multi-step repair or iteration. '
          'Use exploration_start with this workspace, session_id, user objective, a real verifier argv and finite limits. '
          'Read feedback, call exploration_next to reserve an attempt, act using native Codex tools, then exploration_verify. '
          'Verification alone can complete a task. Honor user scope and permissions; do not start loops for unrelated one-shot requests. '
          'Pause on a user stop, unavailable capability or external approval. Never treat tests or tool success as aesthetic review.')


def handle(harness,payload):
    event=payload.get('hook_event_name')
    workspace,session_id=payload.get('cwd'),payload.get('session_id')
    if not isinstance(workspace,str) or not isinstance(session_id,str): return {}
    state=harness.active(workspace,session_id)
    if event=='SessionStart':
        context=GUIDANCE+' Current session_id='+session_id+'.'
        if state: context+=' Existing task: '+json.dumps(summary(state))
        return {'hookSpecificOutput':{'hookEventName':event,'additionalContext':context}}
    if event=='Stop' and state and state['phase'] in ('ready','working'):
        return {'decision':'block','reason':('Continue the explicitly requested exploration task '+state['id']+'. '
                'Read exploration_status. If working, run exploration_verify with the frozen verifier; '
                'if ready, read measured feedback and reserve the next attempt with exploration_next, then act and verify. '
                'Honor scope, limits and any user pause. Do not claim completion before verification passes.')}
    return {}


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--state-dir',default=str(Path.home()/'.codex/exploration-lab/state'))
    args=parser.parse_args()
    try:
        raw=sys.stdin.read(65537)
        if len(raw)>65536: raise ValueError('hook payload too large')
        payload=json.loads(raw)
        harness=Harness(args.state_dir)
        result=handle(harness,payload)
        with (harness.directory/'hook-events.jsonl').open('a') as stream:
            stream.write(json.dumps({'event':payload.get('hook_event_name'),'session_id':payload.get('session_id'),
                                    'output_fields':sorted(result),'time':time.time()})+'\n')
    except Exception:
        result={}
    print(json.dumps(result))


if __name__=='__main__': main()
