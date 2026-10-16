"""Derive live-results retention and recovery facts from actual native UI captures."""
import argparse
import json
import re
from pathlib import Path
from urllib.parse import urlsplit, parse_qs
from email.utils import parsedate_to_datetime

ROOT = Path(__file__).resolve().parents[1]

def page(ax, expected_url, window_uuid, models):
    if 'UUID='+window_uuid not in ax:
        raise ValueError('Wrong owned page window')
    address = next((x for x in ax.splitlines() if 'smart search field' in x), '')
    value = re.search(r'Value: (https://[^\s]+)', address)
    if not value or urlsplit(value[1]) != urlsplit(expected_url):
        raise ValueError('Wrong actual page origin')
    start = re.search(r'^\s*\d+ heading 谁最准, Value: 1$', ax, re.M)
    if not start:
        raise ValueError('Actual leaderboard absent')
    body = ax[start.start():]
    body = body[:body.index('button 展开 AI 模拟速报')]
    if re.search(r'\(showing \d+-\d+ of \d+ items\)', body):
        raise ValueError('Incomplete actual page scope')
    text = ' '.join(re.findall(r'^\s*\d+ text (.+)$', body, re.M))
    scoreboard = text.split('AI 实时积分榜', 1)[1].split('每场对答案', 1)[0]
    scores = {}
    for model in models:
        match = re.search(re.escape(model) + r'\s+(\d+(?:\.\d+)?)\s+分\s+胜负\s+(\d+\.\d+)\s+比分\s+(\d+\.\d+)\s+阵容\s+(\d+\.\d+)\s+KDA\s+(\d+\.\d+)\s+MVP\s+(\d+\.\d+)', scoreboard)
        if not match:
            raise ValueError('Actual model score breakdown unavailable: ' + model)
        scores[model] = list(match.groups())
    updated = re.search(r'赛果更新于\s+(\d+/\d+ \d+:\d+:\d+)', text)
    if not updated:
        raise ValueError('Actual last-good timestamp unavailable')
    return {'scores': scores, 'updated': updated[1],
            'error': '暂时无法加载' in text,
            'retained_notice': '当前保留上次成功加载的数据，请留意更新时间。' in text,
            'stale_notice': '暂用上次赛果' in text,
            'automatic_notice': '自动更新中' in text,
            'refresh_enabled': bool(re.search(r'^\s*\d+ button 立即刷新$', body, re.M)),
            'retry_visible': bool(re.search(r'^\s*\d+ button 重试真实赛果$', body, re.M))}


def request(ax, expected_endpoint, window_uuid):
    if 'UUID='+window_uuid not in ax:
        raise ValueError('Wrong owned request window')
    ax = ax.replace('\u200b', '')
    url = re.search(r'^\s*\d+ text (https://[^\s]+\.json\?t=\d+)$', ax, re.M)
    status = re.search(r'text Status:\s*\n\s*\d+ text (\d+)', ax)
    date = re.search(r'text Date:\s*\n\s*\d+ text (.+)', ax)
    if not url or not status or not date or urlsplit(url[1])._replace(query='') != urlsplit(expected_endpoint):
        raise ValueError('Actual requested endpoint/response unavailable')
    return {'url': url[1], 'minute': int(parse_qs(urlsplit(url[1]).query)['t'][0]),
            'status': int(status[1]), 'response_date': date[1],
            'response_unix': parsedate_to_datetime(date[1]).timestamp()}


def match_details(ax, expected_url, window_uuid, models):
    page(ax, expected_url, window_uuid, models)
    start=re.search(r'^\s*\d+ summary KC 3 : 2 C9 .*, Value: on$',ax,re.M)
    if not start:raise ValueError('Actual requested completed match is not expanded')
    lines=ax.splitlines();summary=next(i for i,line in enumerate(lines) if re.search(r'^\s*\d+ summary KC 3 : 2 C9 .*, Value: on$',line))
    depth=len(lines[summary])-len(lines[summary].lstrip())
    parent=next((i for i in range(summary-1,-1,-1) if 'container (expanded)' in lines[i] and len(lines[i])-len(lines[i].lstrip())<depth),None)
    if parent is not None:
        parent_depth=len(lines[parent])-len(lines[parent].lstrip());end=next((i for i in range(summary+1,len(lines)) if re.match(r'^\s*\d+ ',lines[i]) and len(lines[i])-len(lines[i].lstrip())<=parent_depth),len(lines))
        scope='\n'.join(lines[summary:end])
    else:
        end=re.search(r'^\s*\d+ heading 接下来的比赛，AI 怎么猜',ax[start.end():],re.M)
        if not end:raise ValueError('Actual expanded match scope incomplete')
        scope=ax[start.start():start.end()+end.start()]
    tables=[]
    for part in re.split(r'^\s*\d+ table\s*$',scope,flags=re.M)[1:]:
        rows=[]
        for row in re.split(r'^\s*\d+ row \(selectable\).*$',part,flags=re.M)[1:]:
            cells=re.findall(r'^\s*\d+ cell \(selectable\) (.*?)(?:, Value:.*)?$',row,re.M)
            if cells:rows.append(cells)
        if len(rows)!=len(models) or {x[0] for x in rows}!=set(models):
            raise ValueError('Actual model rows incomplete in match table')
        tables.append(rows)
    headings=re.findall(r'^\s*\d+ heading (第 [1-5] 局 官方 MVP：.*?), Value: 3$',scope,re.M)
    if len(tables)!=6 or len(headings)!=5:raise ValueError('Actual five-game breakdown incomplete')
    return {'interactions':{'match_expanded':True,'all_model_rows_present':True},
            'elements':{'table_'+str(i):{'value':json.dumps(table,ensure_ascii=False)} for i,table in enumerate(tables)} | {'game_headings':{'value':json.dumps(headings,ensure_ascii=False)}}}


def collect(directory, side, window_uuid):
    original = side == 'source'
    original_url = (ROOT/'private/original-share-entry-url.txt').read_text().strip()
    expected_url = original_url if original else 'https://s16.xinxiayiyan.com/?'+urlsplit(original_url).query
    origin = urlsplit(expected_url).netloc
    models = [run['name'] for run in json.loads((ROOT/'private/site/data/index.json').read_text())['runs']]
    endpoint = json.loads((ROOT/'source-build.json').read_text())['live_results_url'] if original else 'https://'+origin+'/content/live-results.json'
    files = {'before': 'source-before-fault-page' if original else 'public-block-applied',
             'failed': 'source-failed-page-2' if original else 'public-failed-page',
             'recovered': side + '-recovered-page'}
    pages = {key: page((directory/(name+'.ax.txt')).read_text(), expected_url, window_uuid, models) for key,name in files.items()}
    request_prefix = 'source-request-' if original else 'public-periodic-request-'
    requests = [request((directory/(request_prefix+str(i)+'-headers.ax.txt')).read_text(), endpoint, window_uuid) for i in (1,2)]
    before, failed, recovered = (pages[x] for x in ('before','failed','recovered'))
    cleanup = (directory/(side+'-block-cleanup.ax.txt')).read_text()
    cleanup_page = page(cleanup, expected_url, window_uuid, models)
    if cleanup_page['error'] or cleanup_page['stale_notice']:
        raise ValueError('Actual cleanup did not leave the owned page healthy')
    interactions = {'failure_visible': failed['error'], 'retained_notice': failed['retained_notice'],
                    'stale_notice': failed['stale_notice'], 'retry_visible': failed['retry_visible'],
                    'scores_retained_on_failure': before['scores'] == failed['scores'],
                    'timestamp_retained_on_failure': before['updated'] == failed['updated'],
                    'recovery_error_cleared': not recovered['error'],
                    'recovery_stale_notice_cleared': not recovered['stale_notice'],
                    'recovery_automatic_notice': recovered['automatic_notice'],
                    'recovery_refresh_enabled': recovered['refresh_enabled'],
                    'temporary_rule_removed': not bool(re.search(r'^\s*\d+ row .*Block', cleanup,re.M)),
                    'consecutive_minute_requests': requests[1]['minute'] == requests[0]['minute']+1,
                    'both_requests_successful': all(x['status']==200 for x in requests)}
    return {'states': {'live_cycle': {'interactions': interactions,
            'elements': {model: {'value': json.dumps(scores)} for model,scores in recovered['scores'].items()}}},
            'pages': pages, 'requests': requests,
            'response_interval_seconds': requests[1]['response_unix']-requests[0]['response_unix']}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('side', choices=['source','public']);p.add_argument('--captures',required=True);p.add_argument('--out',required=True)
    p.add_argument('--window-uuid',required=True)
    p.add_argument('--match-capture', help='Stem of the shared native completed-match capture')
    a=p.parse_args();directory=Path(a.captures).resolve();out=Path(a.out).resolve()
    for path in (directory,out):
        if ROOT/'private' not in path.parents:raise ValueError('Evidence must stay private')
    facts=collect(directory,a.side,a.window_uuid)
    if a.match_capture:
        original_url=(ROOT/'private/original-share-entry-url.txt').read_text().strip()
        expected_url=original_url if a.side=='source' else 'https://s16.xinxiayiyan.com/?'+urlsplit(original_url).query
        models=[run['name'] for run in json.loads((ROOT/'private/site/data/index.json').read_text())['runs']]
        match_path=directory/(a.match_capture+'.ax.txt')
        if directory not in match_path.resolve().parents:raise ValueError('Match evidence must stay in capture directory')
        facts['states']['live_match']=match_details(match_path.read_text(),expected_url,a.window_uuid,models)
        after_match=match_details(match_path.with_name(a.match_capture+'.after.ax.txt').read_text(),expected_url,a.window_uuid,models)
        facts['states']['live_match']['interactions']['match_capture_stable']=facts['states']['live_match']==after_match
    with out.open('x') as f:json.dump(facts,f,ensure_ascii=False,indent=2)
    if a.side=='source':
        requirements=[]
        if not all(value for state in facts['states'].values() for value in state['interactions'].values()):
            raise ValueError('Original behavior preconditions not satisfied; preserve failed evidence')
        for state_name,state in facts['states'].items():
            evidence=str(directory.relative_to(ROOT.parents[1]))+('/'+a.match_capture+'.ax.txt' if state_name=='live_match' else '/source-failed-page-2.ax.txt')
            for name,value in state['interactions'].items():
                requirements.append({'id':state_name+'.'+name,'state':state_name,'kind':'interaction_boolean','field':name,'expected':value,'evidence':[evidence]})
            for name,value in state['elements'].items():
                requirements.append({'id':state_name+'.'+name,'state':state_name,'kind':'element_value','element':name,'value':value['value'],'evidence':[evidence if state_name=='live_match' else str(directory.relative_to(ROOT.parents[1]))+'/source-recovered-page.ax.txt']})
        with out.with_name(out.stem+'-contract.json').open('x') as f:json.dump({'schema_version':1,'scope':'Actual visible-page minute requests and temporary URL-block failure/last-good recovery; no pixel or exact scheduling-jitter claim.','requirements':requirements},f,ensure_ascii=False,indent=2)
    print(json.dumps({'side':a.side,'interactions':facts['states']['live_cycle']['interactions'],'response_interval_seconds':facts['response_interval_seconds']}))


if __name__=='__main__':main()
