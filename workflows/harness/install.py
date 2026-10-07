"""Register reviewed local launchers without replacing unrelated Codex configuration."""
import argparse
import json
import os
from pathlib import Path
import shlex
import subprocess
import sys
import time
import tomllib
from capabilities.exploration.session import save

NAME='exploration-lab'


def install(codex_home,repo_root):
    home,repo=Path(codex_home).resolve(),Path(repo_root).resolve()
    if not (repo/'runtime/harness_mcp.py').is_file(): raise ValueError('validated harness repository required')
    home.mkdir(parents=True,exist_ok=True)
    package=home/NAME
    package.mkdir(exist_ok=True)
    config_path=home/'config.toml'
    config=tomllib.loads(config_path.read_text()) if config_path.exists() else {}
    launcher=package/'mcp.sh'
    old=config.get('mcp_servers',{}).get(NAME)
    if old and (old.get('command')!=str(launcher) or old.get('args',[])!=[]):
        raise ValueError('existing MCP name has another owner')
    hook_path=home/'hooks.json'
    hooks=json.loads(hook_path.read_text()) if hook_path.exists() else {'hooks':{}}
    if not isinstance(hooks.get('hooks'),dict): raise ValueError('invalid existing hooks configuration')
    backup=package/'backups'/str(time.time_ns())
    backup.mkdir(parents=True)
    for path in (config_path,hook_path):
        if path.exists():
            target=backup/path.name
            target.write_bytes(path.read_bytes())
            target.chmod(0o600)
    state=package/'state'
    for name,module in (('mcp','runtime.harness_mcp'),('hook','runtime.harness_hooks')):
        target=package/(name+'.sh')
        content='#!/bin/sh\ncd '+shlex.quote(str(repo))+' || exit 1\nexec '+shlex.quote(sys.executable)+' -m '+module+' --state-dir '+shlex.quote(str(state))+'\n'
        target.write_text(content)
        target.chmod(0o700)
    command=shlex.quote(str(package/'hook.sh'))
    for event in ('SessionStart','Stop','Interrupt','UserPromptSubmit'):
        entries=hooks['hooks'].setdefault(event,[])
        if not any(any(h.get('command')==command for h in entry.get('hooks',[])) for entry in entries):
            entries.append({'hooks':[{'type':'command','command':command,'timeout':3,'statusMessage':'Exploration Lab'}]})
    # Native CLI rewriting can normalize unrelated server definitions. Append only
    # this owned TOML table, preserving every existing byte and semantic value.
    if old is None:
        original=config_path.read_bytes() if config_path.exists() else b''
        table='\n\n[mcp_servers.exploration-lab]\ncommand = '+json.dumps(str(launcher))+'\nargs = []\n'
        temporary=config_path.with_suffix('.exploration.tmp')
        temporary.write_bytes(original+table.encode())
        temporary.chmod(config_path.stat().st_mode & 0o777 if config_path.exists() else 0o600)
        temporary.replace(config_path)
    save(hook_path,hooks)
    after=tomllib.loads(config_path.read_text())
    for key,value in config.items():
        if key=='mcp_servers':
            for server,settings in value.items():
                if server!=NAME and after['mcp_servers'].get(server)!=settings: raise ValueError('unrelated MCP settings changed')
        elif after.get(key)!=value: raise ValueError('unrelated Codex configuration changed')
    return {'mcp_server':NAME,'registered':True,'events':['SessionStart','Stop','Interrupt','UserPromptSubmit'],
            'hook_trust':'requires_native_review','state_directory':str(state),'backup_directory':str(backup)}


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--codex-home',default=str(Path.home()/'.codex'))
    parser.add_argument('--repo',default=str(Path.cwd()))
    parser.add_argument('--out')
    args=parser.parse_args()
    result=install(args.codex_home,args.repo)
    if args.out: Path(args.out).write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if not k.endswith('directory')}))


if __name__=='__main__': main()
