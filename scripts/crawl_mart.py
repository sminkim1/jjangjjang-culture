#!/usr/bin/env python3
"""Public Lotte Mart Gyeyang (469) winter catalog only."""
import concurrent.futures,datetime,json,re,time,urllib.request,urllib.parse
from pathlib import Path
from bs4 import BeautifulSoup
ROOT=Path(__file__).resolve().parents[1];BASE='https://culture.lottemart.com';NOW=datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))).isoformat(timespec='seconds')
def text(e):return e.get_text(' ',strip=True) if e else ''
def fetch(path,params=None):
 for attempt in range(3):
  try:
   req=urllib.request.Request(BASE+path,data=urllib.parse.urlencode(params).encode() if params else None,headers={'User-Agent':'JjangJjangCultureResearch/1.0 (public course comparison)','Referer':BASE+'/cu/branch/main.do?search_str_cd=469'})
   with urllib.request.urlopen(req,timeout=30) as r:return r.read().decode('utf-8','replace')
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
def listing(page):
 s=BeautifulSoup(fetch('/cu/gus/course/courseinfo/searchList.do',dict(search_str_cd='469',search_term_cd='202604',currPageNo=page,search_list_type='')),'html.parser')
 trs=s.select('tr');last=s.select_one('tr[pageinfo]')
 if not last:raise RuntimeError('Missing official pagination')
 pageinfo=[int(x) for x in last['pageinfo'].split('|')];out=[]
 for tr in trs:
  a=tr.select_one('.info-txt a');info=tr.select_one('.info-txt')
  if not a:continue
  ar=age(text(info));code=re.search(r"fn_clsView\('([0-9]+)'\)",a.get('onclick',''));title=text(a).replace('[계양점]','').strip()
  if not ar or ar[0]>=60 or not code:continue
  target=text(info)
  cells=tr.find_all('td',recursive=False)
  n=re.search(r'(\d+)회',text(cells[3]));fees=re.findall(r'([\d,]+)원',text(cells[3]));status=text(tr.select_one('.td-status'))
  out.append(dict(id='m-'+code[1],provider='롯데마트',centerName='롯데마트 문화센터',branch='계양점',city='인천',title=title,minAge=ar[0],maxAge=ar[1],type=category(title+' '+target),url=BASE+'/cu/gus/course/courseinfo/courseview.do?search_str_cd=469&cls_cd='+code[1],teacher=text(cells[1]),sessions=int(n[1]) if n else None,fee=int(fees[0].replace(',','')) if fees else None,feeBasis='할인 전' if len(fees)>1 else '',discountedFee=int(fees[-1].replace(',','')) if len(fees)>1 else None,status='마감임박' if '마감임박' in status else '접수중' if '바로신청' in status else '대기접수' if '대기' in status else '접수마감' if '마감' in status else '미확인',materials=None,materialsNote='재료비 미확인',supplies='공식 상세에서 확인',checkedAt=NOW))
 return out,pageinfo,len(trs)
def detail(c):
 s=BeautifulSoup(fetch(c['url'].removeprefix(BASE)),'html.parser');fields={}
 actual=s.select_one('#frm input[name=cls_cd]')
 if not actual or 'm-'+actual.get('value','')!=c['id']:raise RuntimeError('Wrong detail ID '+c['id'])
 for th in s.select('.tbl_view-area th'):
  fields[text(th)]=text(th.find_next_sibling('td'))
 ds=re.findall(r'\d{4}\.\d{2}\.\d{2}',fields.get('강좌기간',''))
 if len(ds)!=2:raise RuntimeError('Missing period '+c['id'])
 c['start']=ds[0].replace('.','-');c['end']=ds[1].replace('.','-')
 ar=age(fields.get('연령',''))
 if ar:c['minAge'],c['maxAge']=ar
 tm=re.search(r'(\d\d:\d\d)\s*[~\-–]\s*(\d\d:\d\d)',fields.get('강좌시간',''));day=re.search('[월화수목금토일]',fields.get('강좌시간',''))
 c['time']=tm[1]+'–'+tm[2] if tm else None;c['day']=day[0] if day else None
 material=fields.get('재료비/교재비','');c['materialsNote']=material or '재료비 미확인'
 amounts=re.findall(r'([\d,]+)\s*원',material)
 if len(amounts)==1:c['materials']=int(amounts[0].replace(',',''))
 elif re.fullmatch(r'없음|0원|무료|해당없음',material.strip()):c['materials']=0
 if re.search('회당|매회|월별|추가|선택|첫 학기|별도구매|이상|부터',material) or len(amounts)>1:c['materialsUnclear']=True
 c['supplies']=fields.get('첫시간 준비물') or '공식 상세에서 확인'
 if '영아강좌' in fields.get('대상',''):c['participants']='아이1명 + 보호자1명 (영아강좌 2인 기준)'
 elif '보호자도 접수' in c['title']:c['materialsUnclear']=True;c['feeBasis']='1인 · 보호자 별도 접수';c['participants']='보호자도 접수 필요'
 for th in s.select('#lctInfo th, .conts-box th'):
  if text(th)=='강의실':c['room']=text(th.find_next_sibling('td'))
 c['detailChecked']=True;return c
def main():
 rows,pi,cnt=listing(1);total=pi[2];seen=cnt
 with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
  for rs,info,n in pool.map(listing,range(2,pi[1]+1)):rows+=rs;seen+=n
 print('Gyeyang catalog',seen,'/',total,'eligible',len(rows),flush=True)
 if seen!=total:raise RuntimeError('Catalog incomplete')
 with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:rows=list(pool.map(detail,rows))
 data={'checkedAt':NOW,'period':'2026 겨울','courses':rows,'sources':[dict(provider='롯데마트',centerName='롯데마트 문화센터',branch='계양점',city='인천',status='collected',catalogTotal=total,catalogCollected=seen,courses=len(rows),pages=pi[1],url=BASE+'/cu/branch/main.do?search_str_cd=469') ]}
 (ROOT/'data'/'mart.json').write_text(json.dumps(data,ensure_ascii=False,indent=2));print('Saved',len(rows),'Gyeyang courses',flush=True)
if __name__=='__main__':main()
