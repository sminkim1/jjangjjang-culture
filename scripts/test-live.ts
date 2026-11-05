import assert from 'node:assert/strict';
import {collect,initialTasks,age,normalize} from '../server/collectors';
assert.deepEqual(age('오감놀이 5~10개월'),[5,10]);assert.equal(age('성인'),null);
assert.equal(normalize({sessions:1,start:'2026-11-07',materials:0,supplies:'재료비 40,000원'}).materialsUnclear,true);
const initial=initialTasks();assert.equal(initial.length,23);assert.equal(initial.filter(t=>t.p==='롯데마트').length,1);
for(const kind of ['hlist','llist','mlist','slist']){
 const t=initial.find(t=>t.kind===kind&&(kind!=='slist'||t.code==='03'))!;
 const r=await collect(t);assert(r.tasks.length>0,kind+' tasks');const detail=r.tasks.find(t=>t.kind.endsWith('detail')||t.kind==='lgroup');assert(detail,kind+' detail task');let d=await collect(detail!);if(detail!.kind==='lgroup'){assert(d.tasks.length);d=await collect(d.tasks[0]);}assert(d.courses.length,kind+' course');const c=d.courses[0];assert(c.minAge<60);assert(c.start&&c.end);assert(c.checkedAt);console.log(JSON.stringify({provider:t.p,tasks:r.tasks.length,sample:c.id,fee:c.fee,materials:c.materials,status:c.status}));
}
// A changed or blocked source must fail, never replace a provider with an empty success.
const real=globalThis.fetch;globalThis.fetch=async()=>new Response('<html>maintenance</html>');await assert.rejects(()=>collect(initial[0]));globalThis.fetch=real;
console.log('Official collectors and failure safety passed.');
