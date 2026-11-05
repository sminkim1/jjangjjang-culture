import assert from 'node:assert/strict';
import {Miniflare} from 'miniflare';
import {readFile,readdir} from 'node:fs/promises';
import {api} from '../server/refresh';
const mf=new Miniflare({modules:true,script:'export default {fetch(){return new Response("ok")}}',d1Databases:['DB'],r2Buckets:['BUCKET'],cf:false});
const DB=await mf.getD1Database('DB'),BUCKET=await mf.getR2Bucket('BUCKET'),env={DB,BUCKET} as any;
try{
 for(const f of (await readdir('drizzle')).filter(x=>x.endsWith('.sql')).sort())for(const sql of (await readFile('drizzle/'+f,'utf8')).split('--> statement-breakpoint'))if(sql.trim())await DB.prepare(sql).run();
 const req=(path:string,post=false,auth=false)=>new Request('https://test.local'+path,{method:post?'POST':'GET',headers:post?{'Origin':'https://test.local','X-Jjang-Refresh':'1',...(auth?{'oai-authenticated-user-id':'test'}:{})}:{}});
 const call=async(path:string,post=false)=>{const r=await api(req(path,post),env);assert.equal(r.status,200);return r.json() as Promise<any>;};
 assert.equal((await api(new Request('https://test.local/api/refresh',{method:'POST',headers:{'Origin':'https://test.local'}}),env)).status,403);
 assert.equal((await api(new Request('https://test.local/api/refresh',{method:'POST',headers:{'Origin':'https://other.local','X-Jjang-Refresh':'1','oai-authenticated-user-id':'test'}}),env)).status,403);
 assert.equal((await call('/api/catalog')).seed,true);
 const realFetch=globalThis.fetch;
 globalThis.fetch=async(input:any)=>{const u=String(input);return new Response(u.includes('ehyundai')?'<span class="num">0건</span>':u.includes('lotteshopping')?'<div class="no_srch_area" data-tot-cnt="0"></div>':u.includes('lottemart')?'<tr pageInfo="1|0|0|0|0|0"></tr>':JSON.stringify({result:'SUCCESS',param:{totalCount:0},lectList:[]}));};
 const [a,b]=await Promise.all([call('/api/refresh',true),call('/api/refresh',true)]);assert.equal(a.started_at,b.started_at);assert.equal(a.pending,23);
 let s=a;for(let i=0;i<8&&s.status==='running';i++)s=await call('/api/refresh/step',true);assert.equal(s.status,'complete');assert.equal((await call('/api/catalog')).courses.length,0);
 // Failed source retains its previous records and original checkedAt.
 const fixture=JSON.parse(await readFile('public/courses.json','utf8'));await BUCKET.put('fixture.json',JSON.stringify(fixture));await DB.prepare("UPDATE refresh_jobs SET catalog_key='fixture.json'").run();
 globalThis.fetch=async()=>new Response('<html>maintenance</html>');await call('/api/refresh',true);for(let i=0;i<12;i++){s=await call('/api/refresh/step',true);if(s.status!=='running')break;}assert.equal(s.status,'partial');const kept=await call('/api/catalog');assert.equal(kept.courses.length,fixture.courses.length);assert.equal(kept.checkedAt,fixture.checkedAt);
 // Abandoned initialization must recover when a subsequent page steps the job.
 await DB.prepare("UPDATE refresh_jobs SET status='starting',lease=0").run();s=await call('/api/refresh/step',true);assert.equal(s.status,'running');assert(s.pending>0);
 // A live lease is shared rather than starting competing work.
 await DB.prepare("UPDATE refresh_jobs SET lease=?").bind(Date.now()+60000).run();const before=await call('/api/refresh');s=await call('/api/refresh/step',true);assert.equal(s.fence,before.fence);assert.equal(s.pending,before.pending);
 globalThis.fetch=realFetch;
 console.log('D1/R2 integration: anonymous same-origin access, cross-origin rejection, simultaneous loads, full completion, source failure preservation, resume and lease passed.');
}finally{await mf.dispose();}
