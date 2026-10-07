"""Local Codex task state; hooks and tools share the same owner."""
from contextlib import contextmanager
import fcntl
import json
import math
from pathlib import Path
import re
import time
import uuid
from capabilities.exploration.ledger import digest
from capabilities.exploration.session import save

TERMINAL={'complete','blocked','budget_exhausted','paused'}


class Harness:
    def __init__(self,directory):
        self.directory=Path(directory).resolve()
        self.directory.mkdir(parents=True,exist_ok=True)

    @contextmanager
    def lock(self):
        with (self.directory/'lock').open('a') as stream:
            fcntl.flock(stream,fcntl.LOCK_EX)
            yield

    def path(self,task_id):
        if not isinstance(task_id,str) or not re.fullmatch('[a-f0-9]{32}',task_id):
            raise ValueError('invalid task id')
        return self.directory/(task_id+'.json')

    def read(self,task_id):
        return json.loads(self.path(task_id).read_text())

    def write(self,state):
        save(self.path(state['id']),state)
        return state

    def scope(self,workspace,session_id):
        return self.directory/('active-'+digest([str(Path(workspace).resolve()),session_id])+'.json')

    def active(self,workspace,session_id):
        pointer=self.scope(workspace,session_id)
        if not pointer.exists(): return None
        return self.read(json.loads(pointer.read_text())['id'])

    def start(self,*,workspace,session_id,objective,verifier,max_iterations=10,max_failures=3,max_seconds=1800):
        root=Path(workspace).resolve()
        if not root.is_dir(): raise ValueError('explicit existing workspace required')
        if not isinstance(session_id,str) or not 1<=len(session_id)<=128: raise ValueError('session id required')
        if not isinstance(objective,str) or not 1<=len(objective.strip())<=4000: raise ValueError('objective required')
        if not isinstance(verifier,list) or not 1<=len(verifier)<=50 or any(not isinstance(v,str) or not v or len(v)>4096 for v in verifier):
            raise ValueError('explicit verifier argv required')
        for value in (max_iterations,max_failures):
            if isinstance(value,bool) or not isinstance(value,int) or not 1<=value<=100: raise ValueError('iteration and failure bounds in [1,100] required')
        if isinstance(max_seconds,bool) or not isinstance(max_seconds,(int,float)) or not math.isfinite(max_seconds) or not 1<=max_seconds<=86400:
            raise ValueError('finite wall budget in [1,86400] required')
        with self.lock():
            active=self.active(str(root),session_id)
            if active and active['phase'] not in TERMINAL: raise ValueError('an active task already exists; resume or pause it')
            state={'id':uuid.uuid4().hex,'workspace':str(root),'session_id':session_id,'objective':objective,
                   'verifier':verifier,'verifier_digest':digest(verifier),'phase':'ready','iterations':0,
                   'max_iterations':max_iterations,'max_failures':max_failures,'failures':0,
                   'deadline':time.time()+max_seconds,'attempts':[],'last_error':None,'hook_events':[]}
            self.write(state)
            save(self.scope(str(root),session_id),{'id':state['id']})
            return state

    def begin(self,task_id,hypothesis):
        if not isinstance(hypothesis,str) or not 1<=len(hypothesis.strip())<=4000: raise ValueError('hypothesis required')
        with self.lock():
            state=self.read(task_id)
            if state['phase']=='working': return state
            if state['phase']!='ready': raise ValueError('task is not ready')
            if time.time()>=state['deadline'] or state['iterations']>=state['max_iterations']:
                state.update(phase='budget_exhausted',last_error='iteration or wall budget exhausted')
                return self.write(state)
            state['iterations']+=1
            state['attempts'].append({'iteration':state['iterations'],'hypothesis':hypothesis,'evaluation':None})
            state['phase']='working'
            return self.write(state)
