const fs=require('fs'),ts=require('typescript'),assert=require('assert');
require.extensions['.ts']=(m,p)=>m._compile(ts.transpileModule(fs.readFileSync(p,'utf8'),{compilerOptions:{module:ts.ModuleKind.CommonJS,esModuleInterop:true,target:ts.ScriptTarget.ES2020}}).outputText,p);
const {matchingOffers,demoFlyer}=require('../lib/notifications.ts');const {products}=require('../lib/catalog.ts');
let passed=0;function check(value,label){assert(value,label);passed++;console.log('PASS',label)}
check(products.length===733,'733 catalogue cards');check(new Set(products.map(p=>p.id)).size===733,'Unique product IDs');
for(const p of products){check(!!p.image,'photo '+p.id);const ids=new Set(p.offers.map(o=>o.id));assert(p.formats.every(f=>f.offerIds.every(i=>ids.has(i))));assert(new Set(p.formats.map(f=>f.id)).size===p.formats.length)}
for(const o of demoFlyer.offers){if(o.productId){const p=products.find(p=>p.id===o.productId);assert(p);assert(o.formatIds.length);assert(o.formatIds.every(id=>p.formats.some(f=>f.id===id)))}assert(o.page>=1&&o.page<=16);if(o.price!==null)assert(o.price>0)}
const match=(productId,formatId)=>matchingOffers([{productId,formatId}]);
check(match('mulino-bianco-pan-bauletto','bianco-400-g').length===1,'Bianco400g matches');check(match('mulino-bianco-pan-bauletto','integrale-400-g').length===0,'Integrale400g does not match Bianco');check(match('mulino-bianco-pan-bauletto','linea').length===1,'Whole line matches once');
check(match('calve-maionese-classica','238-g').length===0,'Old Calve238g does not match214g');check(match('calve-maionese-classica','214-g').length===1,'Calve214g matches');
check(match('fagolosi480','documented').length===0,'Fagolosi480g does not match250g');check(match('fagolosi480','classici-250-g').length===1,'Fagolosi250g matches');
check(match('mulino-biscuits-macine-range','format-5225ccfad88d75').length===0,'Macine350g does not match1kg');check(match('mulino-biscuits-macine-range','macine-1-kg').length===1,'Macine1kg matches');check(match('mulino-biscuits-macine-range','linea').length===1,'Macine whole line matches');
const dup=matchingOffers([{productId:'mulino-bianco-pan-bauletto',formatId:'linea'},{productId:'mulino-bianco-pan-bauletto',formatId:'bianco-400-g'}]);check(dup.length===1,'Overlapping watchlist choices do not duplicate notifications');
check(matchingOffers([]).length===0,'Empty watchlist no offers');
console.log('All checks passed:',passed);
