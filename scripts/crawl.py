#!/usr/bin/env python3
"""Official public catalogs only; no auth, bypass, or implied empty results.
Run: PYTHONPATH=/private/tmp/jjang-libs python3 scripts/crawl.py
"""
import concurrent.futures, datetime, html, json, re, time, urllib.parse, urllib.request
from pathlib import Path
from bs4 import BeautifulSoup
ROOT=Path(__file__).resolve().parents[1]
NOW=datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))).isoformat(timespec='seconds')
BASE='https://www.ehyundai.com'
ALLOWED={'압구정본점':'서울','무역센터점':'서울','천호점':'서울','신촌점':'서울','미아점':'서울','목동점':'서울','더현대 서울':'서울','중동점':'부천'}
def fetch(url):
 for attempt in range(3):
  try:
   req=urllib.request.Request(url,headers={'User-Agent':'JjangJjangCultureResearch/1.0 (public course comparison)'})
   with urllib.request.urlopen(req,timeout=30) as r:return r.read().decode('utf-8','replace')
  except Exception:
   if attempt==2:raise
   time.sleep(1+attempt)
def text(el):return el.get_text(' ',strip=True) if el else ''
def age(title):
 m=re.search(r'(\d+)\s*[~\-–]\s*(\d+)\s*개월',title)
 if m:return [int(m[1]),int(m[2])]
 m=re.search(r'(\d+)\s*개월\s*이상',title)
 if m:return [int(m[1]),120]
 return None
def category(t):
 if re.search('음악|리듬|유리드믹|악기|뮤직|노래',t):return '음악·리듬'
 if re.search('체육|트니트니|런 &|스포츠|짐|점프|체조|마사지',t):return '신체·움직임'
 if re.search('미술|아트|물감|드로잉|발레',t):return '미술·표현'
 if re.search('몬테소리|글렌도만|영어|영재|언어',t):return '탐색·언어'
 return '오감·통합놀이'
def parse(source):
 soup=BeautifulSoup(source,'html.parser');out=[]
 for li in soup.select('.culture_list ul.list03 > li'):
  a=li.select_one('a[href*="CT010100_V"]');title=text(li.select_one('dt'));ar=age(title)
  if not a or not ar or ar[0]>59:continue
  if re.search(r'개월\s*(습득|학습|과정|수강)',title):continue
  infos=[text(x) for x in li.select('.class_info .info')];full=' '.join(infos)
  br=re.search(r'\[([^]]+)\]',full);branch=br[1] if br else ''
  if branch not in ALLOWED:continue
  ds=re.findall(r'\d{4}\.\d{2}\.\d{2}',full)
  tm=re.search(r'(\d{2}:\d{2})\s*[-~]\s*(\d{2}:\d{2})',full)
  day=re.search(r'매주\s*([월화수목금토일])',full) or re.search(r'\(([월화수목금토일])\)',full)
  n=re.search(r'(\d+)회',full);p=re.sub(r'[^0-9]','',text(li.select_one('.price')))
  url=urllib.parse.urljoin(BASE,a['href']);qp=urllib.parse.parse_qs(urllib.parse.urlparse(url).query)
  out.append(dict(id='h-'+qp['stCd'][0]+'-'+qp['sqCd'][0]+'-'+qp['crsSqNo'][0],provider='현대백화점',branch=branch,city=ALLOWED[branch],title=title,minAge=ar[0],maxAge=ar[1],type=category(title),start=ds[0].replace('.','-') if ds else None,end=ds[-1].replace('.','-') if ds else None,day=day[1] if day else None,time=(tm[1]+'–'+tm[2]) if tm else None,sessions=int(n[1]) if n else None,fee=int(p) if p else None,materials=None,materialsNote='재료비 미확인',status=text(li.select_one('.branch_info .state')),url=url,teacher=text(li.select_one('.class_info .info span:nth-of-type(2)')),description='',supplies='공식 상세에서 확인',checkedAt=NOW))
 count=re.search(r'(\d[\d,]*)건',text(soup.select_one('.num')))
 return out,int(count[1].replace(',','')) if count else None

def main():
 allrows={};reports=[]
 for code,mode in [('ALL',''),('400','CH'),('430','CH'),('210','CH')]:
  params={'stCd':code,'keyword':'025' if code=='ALL' else '','nickCrsNm':'개월','pageSize':100,'ctGubn':mode,'yearGubnSta':2026,'monthGubnSta':'10','yearGubnEnd':2027,'monthGubnEnd':'02','orderGubn':'sta'}
  def page(i):
   u=BASE+'/newCulture/CT/CT010100_L.do?'+urllib.parse.urlencode(dict(params,page=i));b=fetch(u);rows,n=parse(b);return i,rows,n
  first,rows,total=page(1)
  if total is None:raise RuntimeError('Catalog structure changed: missing total')
  for r in rows:allrows[r['id']]=r
  pages=(total+99)//100
  print('현대',mode or '문화센터','total',total,'pages',pages,flush=True)
  with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
   for i,rows,n in pool.map(page,range(2,pages+1)):
    for r in rows:allrows[r['id']]=r
  reports.append({'provider':'현대백화점','catalog':mode or '문화센터','status':'collected','pages':pages,'catalogTotal':total})
 rows=list(allrows.values())
 # Enrich an even spread of baby/older courses across branches; unknown costs stay unknown.
 selected=[]
 for branch in ALLOWED:
  candidates=[r for r in rows if r['branch']==branch]
  candidates.sort(key=lambda r:(r['minAge']>=12,r['day'] not in ['토','일'],r['start'] or ''))
  selected.extend(candidates[:16])
 def detail(r):
  try:
   soup=BeautifulSoup(fetch(r['url']),'html.parser')
   for tr in soup.select('tr'):
    th=tr.find('th');td=tr.find('td')
    if not th or not td:continue
    key=text(th);v=text(td)
    if '재료비' in key:
     m=re.search(r'([\d,]+)\s*원',v)
     if m:r['materials']=int(m[1].replace(',',''));r['materialsNote']=v[:200]
    if '클래스 소개' in key or '강의 개요' in key:r['description']=v[:1800]
    if '준비물' in key and v:r['supplies']=v[:500]
   # Some rows have multiple th/td pairs.
   for th in soup.find_all('th'):
    if '재료비'==text(th):
     v=text(th.find_next_sibling('td'));m=re.search(r'([\d,]+)\s*원',v)
     if m:r['materials']=int(m[1].replace(',',''));r['materialsNote']=v[:200]
   r['materialsIncluded']=bool(re.search(r'재료비[^.\n]{0,30}포함',r.get('description','')))
   if r['materialsNote'] and re.search(r'회당|매회|매주|월별',r['materialsNote']):r['materialsUnclear']=True
   r['detailChecked']=True
  except Exception as e:r['detailError']=str(e)[:120]
  return r
 with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
  for r in pool.map(detail,selected):allrows[r['id']]=r
 data={'checkedAt':NOW,'period':'2026-10 ~ 2027-02','courses':list(allrows.values()),'sources':reports}
 (ROOT/'data'/'hyundai.json').write_text(json.dumps(data,ensure_ascii=False,indent=2))
 print('Saved',len(allrows),'courses; enriched',len(selected),flush=True)
if __name__=='__main__':main()
