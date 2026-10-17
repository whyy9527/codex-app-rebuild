"""Cache only source-catalog icons actually selected by an accepted model lineup."""
import hashlib,json,urllib.request
from concurrent.futures import ThreadPoolExecutor
from causal_series import ROOT,write

def cache():
 path=ROOT/'data/causal/agents.json';catalog=json.loads(path.read_text());selected=set()
 for file in (ROOT/'data/causal').glob('*.json'):
  data=json.loads(file.read_text())
  if 'frames' not in data:continue
  for part in data.get('cases',[data]):
   selected.update(a['agent'] for f in part['frames'] if f.get('lineup') for a in f['lineup'].values())
 def one(name):
  row=catalog['agents'][name];target=ROOT/row['image']
  if not target.exists():
   if not row['source_image'].startswith('https://media.valorant-api.com/agents/'):raise ValueError('Unexpected image origin')
   target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(urllib.request.urlopen(row['source_image'],timeout=30).read())
  row['sha256']=hashlib.sha256(target.read_bytes()).hexdigest();row['bytes']=target.stat().st_size;return name
 with ThreadPoolExecutor(max_workers=4) as pool:list(pool.map(one,selected))
 write(path,catalog);print('Verified selected agent icons:',len(selected))
if __name__=='__main__':cache()
