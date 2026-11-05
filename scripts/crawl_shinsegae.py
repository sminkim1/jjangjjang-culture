#!/usr/bin/env python3
"""Public Shinsegae Academy catalogs. The landing page shows maintenance;
its own documented search endpoint and course detail pages currently respond.
Run: PYTHONPATH=/private/tmp/jjang-libs python3 scripts/crawl_shinsegae.py
"""
import concurrent.futures,datetime,html,json,re,time,urllib.parse,urllib.request
from pathlib import Path
from bs4 import BeautifulSoup
ROOT=Path(__file__).resolve().parents[1]
BASE='https://sacademy.shinsegae.com/sdotcom/'
NOW=datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))).isoformat(timespec='seconds')
BRANCHES={'01':'본점','03':'타임스퀘어점','14':'강남점'}
STATUS={'PR':'접수예정','RT':'접수중','RC':'접수마감','ST':'대기접수','LC':'강의종료'}
def text(e):return e.get_text(' ',strip=True) if e else ''
def fetch(url,params=None):
 for attempt in range(3):
  try:
   req=urllib.request.Request(url,data=urllib.parse.urlencode(params).encode() if params else None,headers={'User-Agent':'JjangJjangCultureResearch/1.0 (public course comparison)','Referer':BASE+'web/HP0010P0/HP0010P0.do','X-Requested-With':'XMLHttpRequest'})
   with urllib.request.urlopen(req,timeout=30) as r:return r.read().decode('utf-8','replace')
  except Exception:
   if attempt==2:raise
   time.sleep(attempt+1)
def age(title):
 m=re.search(r'(\d+)\s*[~\-–]\s*(\d+)\s*개월',title)
 if m:return int(m[1]),int(m[2])
 m=re.search(r'(\d+)\s*개월\s*이상',title)
 if m:return int(m[1]),120
 return None
def category(t):
 if re.search('음악|리듬|유리드믹|악기|뮤직|노래',t):return '음악·리듬'
 if re.search('체육|트니트니|스포츠|짐|점프|체조|마사지',t):return '신체·움직임'
 if re.search('미술|아트|물감|드로잉|발레',t):return '미술·표현'
 if re.search('몬테소리|글렌도만|영어|영재|언어',t):return '탐색·언어'
 return '오감·통합놀이'
def catalog(pair):
 code,term=pair;rows={};total=None;page=1
 while total is None or len(rows)<total:
  params={'storeCode':code,'schSmstCode':term,'yearCode':'2026','smstCode':term,'curPage':page,'srchCndCd':'01','srchWrd':'개월','lectName':'','tchName':'','lectGrType':'','lectGrCode':'','targetCode':'','dayCode':'','lectTimeCode':'','onOffCode':'N','rcptStat':'','ordKey':'lectName','search':'Y','sttlmBtnYn':'Y','autoSeachYn':'Y'}
  obj=json.loads(fetch(BASE+'web/HP0010P0/getLectList.do',params))
  if obj.get('result')!='SUCCESS' or 'totalCount' not in obj.get('param',{}):raise RuntimeError('Search response unavailable: '+code+' '+term)
  total=int(obj['param']['totalCount']);old=len(rows)
  for row in obj.get('lectList',[]):rows[row['lectCode']]=row
  if len(rows)==old:break
  page+=1
 report={'provider':'신세계백화점','centerName':'신세계 아카데미','branch':BRANCHES[code],'branchCode':code,'term':term,'status':'collected' if len(rows)==total else 'partial','catalogTotal':total,'catalogCollected':len(rows),'pages':max(1,page-1),'landingMaintenance':True,'url':BASE+'web/HP0010P0/HP0010P0.do?storeCode='+code,'note':'화면 시스템 점검 안내 표시 중. 공식 화면의 공개 검색 API 및 상세 페이지에서 수집. 명시 월령 키워드 검색 결과 기준.'}
 print(code,term,len(rows),'/',total,flush=True)
 return list(rows.values()),report

def detail(r):
 ar=age(r['lectName'])
 if not ar or ar[0]>=60:return None
 url=BASE+'web/HP0010P0/HP0010P1.do?'+urllib.parse.urlencode({k:r[k] for k in ['yearCode','smstCode','storeCode','lectCode']})
 soup=BeautifulSoup(fetch(url),'html.parser');values={}
 for tr in soup.select('tr'):
  th=tr.find('th');td=tr.find('td')
  if th and td and text(th) not in values:values[text(th)]=text(td)
 feeText=values.get('수강료','');materialText=values.get('교재/재료비','')
 def amount(s):
  m=re.search(r'([\d,]+)\s*원',s)
  return int(m[1].replace(',','')) if m else (0 if '무료' in s else None)
 fee=amount(feeText);materials=amount(materialText)
 minParticipants=int(r.get('minRecvCnt') or 1);perPerson='1인 기준' in feeText
 extra=[];description='';supplies=''
 for h in soup.find_all('h3'):
  title=text(h);body=h.find_next_sibling()
  if '강좌소개' in title:description=text(body)
  if '첫시간 안내사항' in title:supplies=text(body)
  if '커리큘럼' in title:
   for tr in body.select('tbody tr') if body else []:
    cells=tr.find_all('td')
    if len(cells)>=4 and text(cells[-1]) not in extra:extra.append(text(cells[-1]))
 if extra:supplies+=' / 회차별 준비물: '+' / '.join(extra)
 if not supplies:supplies='공식 상세에서 확인'
 dates=re.findall(r'\d{4}\.\d{2}\.\d{2}',values.get('수강기간') or r.get('lectPeriod',''))
 timeText=values.get('요일/시간','');tm=re.search(r'(\d\d:\d\d)\s*[~–-]\s*(\d\d:\d\d)',timeText)
 # A family total is left unconfirmed when the official price is per person.
 unclear=perPerson and minParticipants>1
 participant=(values.get('수강대상') or '')+' · 최소 '+str(minParticipants)+'인 수강 필요'
 note=materialText+' / '+feeText
 return dict(id='s-'+r['storeCode']+'-'+r['yearCode']+'-'+r['smstCode']+'-'+r['lectCode'],provider='신세계백화점',centerName='신세계 아카데미',branch=BRANCHES[r['storeCode']],city='서울',title=html.unescape(r['lectName']),minAge=ar[0],maxAge=ar[1],type=category(r['lectName']),start=dates[0].replace('.','-') if dates else None,end=dates[-1].replace('.','-') if dates else None,day=r.get('dayCodeName'),time=tm[1]+'–'+tm[2] if tm else None,sessions=int(r['lectCnt']) if r.get('lectCnt') else None,fee=fee,materials=materials,materialsNote=note[:650],materialsUnclear=unclear,feeBasis='1인 기준' if perPerson else '공식 상세 기준',minParticipants=minParticipants,participants=participant,room=values.get('강의실'),status=STATUS.get(r.get('lectStat'),'미확인'),url=url,teacher=r.get('tchName'),description=description[:1800],supplies=supplies[:1600],checkedAt=NOW,detailChecked=True,registration=values.get('접수기간'),capacity=None,remainingSeats=None)

def main():
 rows=[];reports=[];failures=[]
 with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
  for result,report in pool.map(catalog,[(c,s) for c in BRANCHES for s in ['S3','S4']]):rows.extend(result);reports.append(report)
 eligible=[r for r in rows if age(r['lectName']) and age(r['lectName'])[0]<60]
 def safe(r):
  try:return detail(r),None
  except Exception as e:return None,{'lectCode':r['lectCode'],'error':str(e)[:180]}
 courses=[]
 with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
  for i,(row,error) in enumerate(pool.map(safe,eligible),1):
   if row:courses.append(row)
   if error:failures.append(error)
   if i%50==0:print('details',i,'/',len(eligible),flush=True)
 data={'checkedAt':NOW,'period':'2026 가을·겨울학기','courses':courses,'sources':reports,'failures':failures,'landingMaintenance':True}
 (ROOT/'data').mkdir(exist_ok=True);(ROOT/'data'/'shinsegae.json').write_text(json.dumps(data,ensure_ascii=False,indent=2))
 print('Saved',len(courses),'courses;',len(failures),'failures',flush=True)
if __name__=='__main__':main()
