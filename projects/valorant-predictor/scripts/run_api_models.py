"""Use already configured provider credentials; exact runtime model required."""
import argparse
import json
import os
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError
from run_models import normalize, ROOT

PROVIDERS={
    'deepseek':{'base':'https://api.deepseek.com','key':'DEEPSEEK_API_KEY','model':'deepseek-flash','channel':'deepseek','display':'DeepSeek-V4.1-Flash'},
    'doubao':{'base':'https://ark.cn-beijing.volces.com/api/v3','key':'ARK_API_KEY','model':'doubao-seed-2-1-pro-260915','channel':'doubao','display':None},
    'mimo':{'base':'https://api.xiaomimimo.com/v1','key':'MIMO_API_KEY','model':'mimo-v2.6-pro','channel':'mimo','display':None}
}


def request(url,key,body=None,timeout=180):
    headers={'Content-Type':'application/json'}
    if url.startswith('https://api.xiaomimimo.com/v1/'):
        headers['api-key']=key
    else:
        headers['Authorization']='Bearer '+key
    raw=None if body is None else json.dumps(body).encode()
    try:
        with urlopen(Request(url,headers=headers,data=raw),timeout=timeout) as response:return json.load(response)
    except HTTPError as error:
        try:
            detail=json.loads(error.read()).get('error',{})
            raise RuntimeError('Provider HTTP '+str(error.code)+'; code='+str(detail.get('code'))) from None
        except ValueError:raise RuntimeError('Provider HTTP '+str(error.code)) from None


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--provider',choices=list(PROVIDERS),required=True);parser.add_argument('--prompt',type=Path,required=True);parser.add_argument('--out',type=Path,required=True);args=parser.parse_args()
    config=PROVIDERS[args.provider];args.out.mkdir(parents=True,exist_ok=False)
    key=os.environ.get(config['key'])
    if not key:raise RuntimeError('Required provider credential not configured')
    event=json.loads((ROOT/'data/event.json').read_text());prompt=args.prompt.read_text()
    models=request(config['base']+'/models',key)
    exact=next((m for m in models.get('data',[]) if m.get('id')==config['model']),None)
    if not exact or config['display'] and exact.get('name')!=config['display']:raise RuntimeError('Matching model not available from provider catalog')
    (args.out/'model-catalog-entry.json').write_text(json.dumps(exact,ensure_ascii=False,indent=2)+'\n')
    body={'model':config['model'],'messages':[{'role':'user','content':prompt}],'response_format':{'type':'json_object'},'max_tokens':16384}
    if args.provider=='deepseek':body['thinking']={'type':'enabled'};body['reasoning_effort']='high'
    if args.provider=='mimo':body.pop('response_format',None)
    response=request(config['base']+'/chat/completions',key,body)
    (args.out/'response.json').write_text(json.dumps(response,ensure_ascii=False,indent=2)+'\n')
    if response.get('model')!=config['model']:raise RuntimeError('Runtime model mismatch; output rejected')
    choice=response['choices'][0]
    if choice.get('finish_reason')!='stop':raise RuntimeError('Model output was not completed')
    value=json.loads(choice['message']['content'])
    normalized=normalize(value,event,config['model'],config['channel'],{'provider':args.provider,'model':response['model'],
                           'catalog_name':exact.get('name'),'model_mapping_source':'https://api-docs.deepseek.com/news/news260910/' if args.provider=='deepseek' else config['base']+'/models'})
    (args.out/'validated-forecast.json').write_text(json.dumps(normalized,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'provider':args.provider,'model':response['model'],'pairs':len(normalized['pairs']),'out':str(args.out)},ensure_ascii=False))


if __name__=='__main__':
    try:main()
    except HTTPError as error:
        # Never print authorization headers or raw request bodies.
        raise SystemExit('Provider request failed: HTTP '+str(error.code))
