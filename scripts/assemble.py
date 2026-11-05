#!/usr/bin/env python3
"""Normalize snapshot, detect contradictory fees, write offline-ready data/HTML."""
import json,re,datetime,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];DIST=ROOT/'public'
datasets=[json.loads((ROOT/'data'/name).read_text()) for name in ['hyundai.json','lotte.json','mart.json','shinsegae.json'] if (ROOT/'data'/name).exists()]
courses=[c for ds in datasets for c in ds['courses']];sources=[s for ds in datasets for s in ds.get('sources',[])]
for c in courses:
 if c['provider']=='현대백화점':c['centerName']='CH1985' if c['branch'] in ['더현대 서울','중동점','압구정본점'] else '현대백화점 문화센터'
branches=[]
for name,code,city in [('더현대 서울','400','서울'),('압구정본점','210','서울'),('중동점','430','부천'),('무역센터점','220','서울'),('천호점','260','서울'),('신촌점','270','서울'),('미아점','410','서울'),('목동점','420','서울')]:
 branches.append(dict(provider='현대백화점',branch=name,city=city,centerName='CH1985' if code in ['400','210','430'] else '현대백화점 문화센터',url='https://www.ehyundai.com/newCulture/CT/CT010100_L.do?stCd='+code+('&ctGubn=CH' if code in ['400','210','430'] else '')))
for code,name,city in [('0002','잠실점','서울'),('0001','본점','서울'),('0013','강남점','서울'),('0028','건대스타시티점','서울'),('0006','관악점','서울'),('0340','김포공항점','서울'),('0022','노원점','서울'),('0026','미아점','서울'),('0010','영등포점','서울'),('0004','청량리점','서울'),('0344','인천점','인천'),('0334','중동점','부천')]:
 branches.append(dict(provider='롯데백화점',branch=name,city=city,centerName='롯데문화센터',url='https://culture.lotteshopping.com/application/search/list.do?brchCd='+code+'&type=branch'))
for code,name in [('01','본점'),('14','강남점'),('03','타임스퀘어점')]:
 branches.append(dict(provider='신세계백화점',branch=name,city='서울',centerName='신세계 아카데미',url='https://sacademy.shinsegae.com/sdotcom/web/HP0010P0/HP0010P0.do?storeCode='+code))
branches.append(dict(provider='롯데마트',branch='계양점',city='인천',centerName='롯데마트 문화센터',url='https://culture.lottemart.com/cu/branch/main.do?search_str_cd=469'))
for c in courses:
 desc=c.get('description','');supplies=c.get('supplies','');body=desc+' '+supplies
 # A catalog field showing zero can coexist with a separately charged material fee.
 mentions=[]
 for m in re.finditer(r'재료비\s*[:：]?\s*([\d,]+)\s*원',body):
  if int(m[1].replace(',',''))>0:mentions.append(int(m[1].replace(',','')))
 if mentions and c.get('materials') is not None and any(v!=c['materials'] for v in mentions):
  c['materialsUnclear']=True;c['materialsIncluded']=False;c['materialsNote']='상세 본문에 재료비 '+', '.join(f'{n:,}원' for n in sorted(set(mentions)))+' 표기 · 비용 표와 상이하여 센터 확인 필요'
 if c.get('materialsIncluded') and re.search(r'재료비[^.\n]{0,30}별도',body):
  c['materialsUnclear']=True;c['materialsNote']='재료비 포함/별도 문구가 함께 있어 센터 확인 필요'
 if c.get('materials')==0 and re.search(r'재료비[^.\n]{0,35}(별도|문의|매회|매주)',body):
  c['materialsUnclear']=True
 if not c.get('materialsUnclear') and c.get('materials')==0:c['materialsNote']='별도 재료비 0원 (공식 비용표 기준)'
 c['description']='' # Official descriptions can contain broad development claims; UI uses original-source links.
# Exclude adult course study-experience months and unidentified age ranges.
courses=[c for c in courses if (c['provider']!='롯데마트' or c['branch']=='계양점') and c.get('minAge') is not None and c.get('maxAge') is not None and not re.search(r'개월\s*(습득|학습|과정|수강)',c['title'])]
unique={c['id']:c for c in courses}
data={'checkedAt':max(c.get('checkedAt','') for c in courses),'branches':branches,'courses':list(unique.values()),'sources':sources,'snapshot':all(ds.get('snapshot',True) for ds in datasets),'providerRefresh':[p for ds in datasets for p in ds.get('providerRefresh',[])],'limitNotes':['신세계 아카데미 검색 API 수집 완료·홈페이지 점검 안내 지속','롯데마트는 계양점만 포함','실시간 잔여석 미확인','신세계 1인 기준 수강료·최소 참여인원 확인 필요']}
payload=json.dumps(data,ensure_ascii=False).replace('<','\\u003c')
(DIST/'data.js').write_text('window.CULTURE_DATA = '+payload+';')
(DIST/'courses.json').write_text(json.dumps(data,ensure_ascii=False,indent=2))
template=re.sub(r'(style\.css|app\.js|data\.js)\?v=[0-9a-f]+',r'\1',(DIST/'index.html').read_text())
versioned=template
for asset in ['style.css','app.js','data.js']:
 digest=hashlib.sha256((DIST/asset).read_bytes()).hexdigest()[:12]
 versioned=versioned.replace(asset,asset+'?v='+digest)
(DIST/'index.html').write_text(versioned)
page=template.replace('<link rel="stylesheet" href="style.css">','<style>'+(DIST/'style.css').read_text()+'</style>').replace('<script src="data.js"></script>','<script>window.CULTURE_DATA = '+payload+';</script>').replace('<script src="app.js"></script>','<script>'+(DIST/'app.js').read_text()+'</script>')
(ROOT/'짱짱이-문화센터.html').write_text(page)
print(json.dumps({'courses':len(unique),'providers':{p:sum(c['provider']==p for c in unique.values()) for p in set(c['provider'] for c in unique.values())},'materialConflicts':sum(bool(c.get('materialsUnclear')) for c in unique.values())},ensure_ascii=False))
