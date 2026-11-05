#!/usr/bin/env python3
"""Collect public 2026 winter Lotte catalogs; expand each selectable session.
Run: PYTHONPATH=/private/tmp/jjang-libs python3 scripts/crawl_lotte.py --refresh
Omit --refresh to resume from the local research cache.
"""
import concurrent.futures, datetime, json, re, time, urllib.parse, urllib.request, hashlib, html, sys
from pathlib import Path
from bs4 import BeautifulSoup
ROOT=Path(__file__).resolve().parents[1]
BASE='https://culture.lotteshopping.com'
CACHE=ROOT/'research'/'silver-cache';CACHE.mkdir(parents=True,exist_ok=True)
REFRESH='--refresh' in sys.argv
NOW=datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))).isoformat(timespec='seconds')
BRANCHES={'0002':('잠실점','서울'),'0001':('본점','서울'),'0013':('강남점','서울'),'0028':('건대스타시티점','서울'),'0006':('관악점','서울'),'0340':('김포공항점','서울'),'0022':('노원점','서울'),'0026':('미아점','서울'),'0010':('영등포점','서울'),'0004':('청량리점','서울'),'0344':('인천점','인천'),'0334':('중동점','부천')}
def txt(e):return e.get_text(' ',strip=True) if e else ''
def fetch(url,params=None):
 cache=CACHE/(hashlib.sha256((url+json.dumps(params,sort_keys=True)).encode()).hexdigest()+'.txt')
 if cache.exists() and not REFRESH:return cache.read_text()
 for attempt in range(3):
  try:
   req=urllib.request.Request(url,data=urllib.parse.urlencode(params).encode() if params is not None else None,headers={'User-Agent':'JjangJjangCultureResearch/1.0 (public course comparison)','Referer':BASE+'/index.do'})
   with urllib.request.urlopen(req,timeout=30) as r:body=r.read().decode('utf-8','replace')
   cache.write_text(body);return body
  except Exception:
   if attempt==2:raise
   time.sleep(attempt+1)
def age(s):
 m=re.search(r'(\d+)\s*[~\-–]\s*(\d+)\s*개월',s)
 if m:return int(m[1]),int(m[2])
 m=re.search(r'(\d+)\s*개월\s*이상',s)
 if m:return int(m[1]),120
 return None
def category(s):
 if re.search('음악|리듬|유리드믹|악기|뮤직|노래',s):return '음악·리듬'
 if re.search('체육|트니트니|스포츠|짐|점프|체조|마사지',s):return '신체·움직임'
 if re.search('미술|아트|물감|드로잉|발레',s):return '미술·표현'
 if re.search('몬테소리|글렌도만|영어|영재|언어',s):return '탐색·언어'
 return '오감·통합놀이'
def url_for(code,lect):return BASE+'/application/search/view.do?'+urllib.parse.urlencode({'brchCd':code,'yy':2026,'lectSmsterCd':4,'lectCd':lect})
def catalog(code):
 urls={};total=None;page=1
 while total is None or len(urls)<total:
  params={'type':'branch','brchCd':code,'lrclsCtegryCd':'02','yyList':'2026||4','orderSet':'C','pageIndex':page,'initIndex':page,'listCnt':20}
  soup=BeautifulSoup(fetch(BASE+'/search/list.ajax',params),'html.parser');cards=soup.select('.card_list_v[data-tot-cnt]')
  if not cards:
   empty=soup.select_one('.no_srch_area[data-tot-cnt="0"]')
   if empty:total=0;page+=1;break
   raise RuntimeError('Catalog structure changed '+code)
  total=int(cards[0]['data-tot-cnt']);before=len(urls)
  for card in cards:
   a=card.select_one('a.lec_list[href]')
   if a:urls[urllib.parse.urljoin(BASE,a['href'])]=txt(card.select_one('.label'))
  if len(urls)==before:break
  page+=1
 report={'provider':'롯데백화점','branch':BRANCHES[code][0],'status':'collected' if len(urls)==total else 'partial','catalogTotal':total,'catalogCollected':len(urls),'pages':page-1,'url':BASE+'/application/search/list.do?brchCd='+code+'&type=branch'}
 print(code,'catalog',len(urls),'/',total,flush=True)
 return code,urls,report

def parse_detail(url,source,status_hint='미확인'):
 soup=BeautifulSoup(source,'html.parser');v=lambda c:txt(soup.select_one('.'+c))
 qp=urllib.parse.parse_qs(urllib.parse.urlparse(url).query);code=qp['brchCd'][0];lect=qp['lectCd'][0]
 ar=age(v('chldAge'));row=None
 if ar and ar[0]<60:
  title=v('lectNm');times=v('lectTime');tm=re.search(r'(\d\d:\d\d)\s*[-~–]\s*(\d\d:\d\d)',times);day=re.search('[월화수목금토일]',times)
  ds=re.findall(r'\d{4}\.\d{2}\.\d{2}',v('lectStDtm'));count=re.search(r'(\d+)회',v('lectNbcnt'));price=re.sub('[^0-9]','',v('lectAmt'))
  notes=' '.join(txt(n) for n in soup.select('.info_dot_txt .dot_txt'))
  options=[]
  for a in soup.select('a[href*="optionSet"]'):
   match=re.search(r"optionSet\('([^']*)',\s*'(\d+)'",a['href'])
   if match and re.search('재료|교재|대여',match[1]):options.append((int(match[2]),txt(a)))
  amounts=set(n for n,_ in options);materials=next(iter(amounts)) if len(amounts)==1 else None
  note=' / '.join(n for _,n in options) if options else '재료비 미확인'
  if materials is None:
   m=re.search(r'(?:재료비|교재비)[^\d]{0,35}([\d,]+)\s*원',notes)
   if m:materials=int(m[1].replace(',',''));note=m[0]
  button=v('lectStatCd');status={'수강 신청하기':'접수중','대기접수 신청하기':'대기접수','대기 신청하기':'대기접수'}.get(button,button or status_hint)
  row=dict(id='l-'+code+'-2026-4-'+lect,provider='롯데백화점',branch=BRANCHES[code][0],city=BRANCHES[code][1],title=title,minAge=ar[0],maxAge=ar[1],type=category(title),start=ds[0].replace('.','-') if ds else None,end=ds[-1].replace('.','-') if ds else None,day=day[0] if day else None,time=tm[1]+'–'+tm[2] if tm else None,sessions=int(count[1]) if count else None,fee=int(price) if price else None,materials=materials,materialsNote=note[:300],status=status,url=url,teacher=v('tcNm'),description=txt(soup.select_one('.info_img_txt'))[:1800],supplies=notes[:1000] or '공식 상세에서 확인',checkedAt=NOW,detailChecked=True,room=v('lectRmNm'),participants=v('objClNm'),registration=v('rceptPrdStDt'),capacity=None)
 expanded={}
 for a in soup.select('a[href*="classInfoSet"]'):
  m=re.search(r"classInfoSet\('(\d+)',\s*'(\d+)',\s*'(\d+)',\s*'(\d+)'",a['href'])
  # Only target ages, avoid the default 'select' placeholder.
  optage=age(txt(a))
  if m and optage and optage[0]<60:expanded[url_for(m[1],m[4])]=status_hint
 return row,expanded

def parse_api(url):
 qp=urllib.parse.parse_qs(urllib.parse.urlparse(url).query);params={k:v[0] for k,v in qp.items()}
 api=BASE+'/application/search/view.ajax'
 d=json.loads(fetch(api,params)).get('classDtl')
 cache_file=CACHE/(hashlib.sha256((api+json.dumps(params,sort_keys=True)).encode()).hexdigest()+'.txt')
 verified=datetime.datetime.fromtimestamp(cache_file.stat().st_mtime,datetime.timezone(datetime.timedelta(hours=9))).isoformat(timespec='seconds')
 if not d:raise RuntimeError('Missing classDtl')
 ar=age(d.get('chldAge') or '')
 if not ar or ar[0]>=60:return None
 clean=lambda value:txt(BeautifulSoup(html.unescape(value or ''),'html.parser'))
 options=[o for o in d.get('optionList',[]) if re.search('재료|교재|대여',o.get('optnNm') or '')]
 amounts={int(o['optnAmt']) for o in options};materials=next(iter(amounts)) if len(amounts)==1 else None
 notes=' / '.join(clean(o['optnNm'])+' '+format(int(o['optnAmt']),',')+'원' for o in options) or '재료비 미확인'
 content=' '.join(clean(c.get('webCont')) for c in d.get('contentList',[]))
 supplies=' / '.join(clean(x.get('unuslMtrVal')) for x in d.get('unusList',[]))
 if d.get('memoCont'):supplies+=' / '+clean(d.get('memoCont'))
 materialsUnclear=False
 # Text-only material fees are not assumed zero when no structured option exists.
 if materials is None:
  m=re.search(r'(?:재료비|교재비)[^\d]{0,35}([\d,]+)\s*원',supplies)
  if m:
   materials=int(m[1].replace(',',''));notes=m[0]
   materialsUnclear=bool(re.search('회당|매회|1회|월별|매월',m[0]))
 code=d['brchCd'];title=clean(d['lectNm']);day=d.get('stringStDaywNm') or d.get('stDaywNm')
 return dict(id='l-'+code+'-2026-4-'+d['lectCd'],provider='롯데백화점',branch=BRANCHES[code][0],city=BRANCHES[code][1],title=title,minAge=ar[0],maxAge=ar[1],type=category(title),start=(d.get('lectStDtm') or '').replace('.','-') or None,end=(d.get('lectEndDtm') or '').replace('.','-') or None,day=day,time=(d.get('lectSt')+'–'+d.get('lectEnd')) if d.get('lectSt') and d.get('lectEnd') else None,sessions=d.get('lectNbcnt'),fee=d.get('lectAmt'),materials=materials,materialsNote=notes[:300],materialsUnclear=materialsUnclear,status=d.get('lectStatNm') or '미확인',url=url,teacher=clean(d.get('tcNm')),description=content[:1800],supplies=supplies[:1600] or '공식 상세에서 확인',checkedAt=verified,detailChecked=True,room=d.get('lectRmNm'),participants=d.get('objClNm'),registration=(d.get('rceptPrdStDt') or '')+'~'+(d.get('rceptPrdEndDt') or ''),capacity=d.get('gsCapaCnt'),remainingSeats=None)

def main():
 allurls={};reports=[];failures=[];rows={};specific={}
 with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
  for code,urls,report in pool.map(catalog,BRANCHES):allurls.update(urls);reports.append(report)
 def groups(item):
  url,hint=item
  try:
   source=fetch(url);row,expanded=parse_detail(url,source,hint)
   if not expanded:expanded={url:hint}
   return expanded,None
  except Exception as e:return {},{'url':url,'error':str(e)[:180]}
 with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
  for i,(expanded,error) in enumerate(pool.map(groups,allurls.items()),1):
   specific.update(expanded)
   if error:failures.append(error)
   if i%100==0:print('Groups',i,'/',len(allurls),'specific',len(specific),flush=True)
 def detail(url):
  try:return parse_api(url),None
  except Exception as e:return None,{'url':url,'error':str(e)[:180]}
 with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
  for i,(row,error) in enumerate(pool.map(detail,specific),1):
   if row:rows[row['id']]=row
   if error:failures.append(error)
   if i%200==0:print('API details',i,'/',len(specific),'eligible',len(rows),flush=True)
 data={'checkedAt':min((r['checkedAt'] for r in rows.values()),default=NOW),'period':'2026 겨울학기','courses':list(rows.values()),'sources':reports,'failures':failures}
 (ROOT/'data'/'lotte.json').write_text(json.dumps(data,ensure_ascii=False,indent=2))
 print('Saved',len(rows),'courses;',len(failures),'failures',flush=True)
if __name__=='__main__':main()
