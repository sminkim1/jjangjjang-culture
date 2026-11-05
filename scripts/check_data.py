#!/usr/bin/env python3
"""Validate invariants that can silently corrupt course comparison."""
import json,datetime,re,urllib.parse
from pathlib import Path
root=Path(__file__).resolve().parents[1]
x=json.loads((root/'public/courses.json').read_text());rows=x['courses'];assert rows
branches=x.get('branches',[]);assert len({(b['provider'],b['branch']) for b in branches})==len(branches)
assert all(b['branch']=='계양점' for b in branches if b['provider']=='롯데마트')
assert all(any(b['provider']==r['provider'] and b['branch']==r['branch'] for b in branches) for r in rows)
assert len({r['id'] for r in rows})==len(rows),'Duplicate course IDs'
allowed={'www.ehyundai.com','www.e-hyundai.com','culture.lotteshopping.com','culture.lottemart.com','sacademy.shinsegae.com'}
for r in rows:
 if r['provider']=='롯데마트':assert r['branch']=='계양점',r['id']
 assert r['city'] in ['서울','인천','부천'],r['id']
 if r['provider']=='현대백화점' and r['branch']=='더현대 서울':assert r['centerName']=='CH1985'
 if r['provider']=='신세계백화점':assert r['centerName']=='신세계 아카데미'
 assert 0<=r['minAge']<=r['maxAge'],r['id']
 assert not re.search(r'개월\s*(습득|학습|과정|수강)',r['title']),r['id']
 assert urllib.parse.urlparse(r['url']).hostname in allowed,r['id']
 start=datetime.date.fromisoformat(r['start']);end=datetime.date.fromisoformat(r['end'])
 assert start<=end,r['id']
 if r.get('sessions')==1 and r['day'] in '월화수목금토일':assert '월화수목금토일'[start.weekday()]==r['day'],r['id']
 assert r.get('fee') is None or r['fee']>=0,r['id']
 assert r.get('materials') is None or r['materials']>=0,r['id']
js=(root/'public/data.js').read_text();encoded=js.removeprefix('window.CULTURE_DATA = ').removesuffix(';')
assert json.loads(encoded)==x,'Data JSON and browser snapshot differ'
print(f'PASS: {len(rows)} unique courses; geography, ages, dates, one-off weekdays, amounts, source hosts, JSON/JS consistency')
