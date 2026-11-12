import rules from './catalog-match-rules.json'
import {products,Saved} from './catalog'
import {createHash} from 'node:crypto'
export type ExtractedOffer={id:string;page:number;price:number;rawText:string;name:string;condition:string;productId:string;formatIds:string[];status:'candidate'|'matched'}
export type Extraction={title:string;region:string;validFrom:string;validTo:string;source:string;checkedAt:string;sha256:string;pages:number;textItems:number;offers:ExtractedOffer[];warnings:string[]}
const INDEX='https://www.ekomdiscount.it/ebsn/api/leaflet/search?parent_leaflet_type_id=1'
type Item={text:string;x:number;y:number;size:number}
export function normalize(s:string){return s.normalize('NFKD').replace(/[\u0300-\u036f]/g,'').toLowerCase().replace(/[^a-z0-9]+/g,' ').trim()}
async function fetchLimited(url:string,max:number){const r=await fetch(url,{cache:'no-store',signal:AbortSignal.timeout(20000),headers:{'User-Agent':'MioProdotto-test/1.0'}});if(!r.ok)throw Error(`Fonte Ekom non disponibile (${r.status}).`);const len=Number(r.headers.get('content-length')||0);if(len>max)throw Error('Documento troppo grande per questa prova.');const b=new Uint8Array(await r.arrayBuffer());if(b.length>max)throw Error('Documento troppo grande per questa prova.');return b}
export async function latestExtraction():Promise<Extraction>{
 const index=JSON.parse(new TextDecoder().decode(await fetchLimited(INDEX,2_000_000)))
 const current=(index.data?.leaflets||[]).filter((v:any)=>typeof v.location==='string'&&v.location.endsWith('-LGPM.pdf')&&/^https:\/\/app\.ekomdiscount\.it\//.test(v.baseLocation||''))
 current.sort((a:any,b:any)=>String(b.validateDateFrom).localeCompare(String(a.validateDateFrom))||Number(b.leafletId)-Number(a.leafletId))
 const v=current[0];if(!v)throw Error('Nessun PDF Liguria/Piemonte trovato nella fonte Ekom.')
 const url=new URL(v.location,v.baseLocation.endsWith('/')?v.baseLocation:v.baseLocation+'/');if(url.origin!=='https://app.ekomdiscount.it'||!url.pathname.endsWith('.pdf'))throw Error('Indirizzo PDF della fonte non riconosciuto.')
 const bytes=await fetchLimited(url.href,25_000_000);if(new TextDecoder().decode(bytes.slice(0,4))!=='%PDF')throw Error('La fonte non ha restituito un PDF.')
 const read=await extractPDF(bytes)
 return {title:v.title||v.name||'Volantino Ekom',region:'Liguria e Piemonte',validFrom:String(v.validateDateFrom).slice(0,10),validTo:String(v.validateDateTo).slice(0,10),source:url.href,checkedAt:new Date().toISOString(),sha256:createHash('sha256').update(bytes).digest('hex'),...read}
}
export async function extractPDF(bytes:Uint8Array){
 const {getDocument}=await import('pdfjs-dist/legacy/build/pdf.mjs')
 const doc=await getDocument({data:bytes.slice(),useSystemFonts:true,isEvalSupported:false,disableFontFace:true}).promise
 if(doc.numPages>40)throw Error('Il PDF supera le 40 pagine supportate nella prova.')
 let textItems=0;const offers:ExtractedOffer[]=[];const warnings:string[]=[]
 for(let p=1;p<=doc.numPages;p++){
  const page=await doc.getPage(p),content=await page.getTextContent();const items:Item[]=content.items.filter((x:any)=>x.str?.trim()).map((x:any)=>({text:x.str.trim(),x:x.transform[4],y:page.view[3]-x.transform[5],size:Math.hypot(x.transform[0],x.transform[1])}));textItems+=items.length
  const pageText=normalize(items.map(i=>i.text).join(' '));const condition=pageText.includes('possessori')&&pageText.includes('ekom up')?'Solo possessori EKOM UP':pageText.includes('vendita assistita')?'Solo reparti con vendita assistita':'';
  const prices=items.filter(i=>i.size>=23&&/^\d+[,.]\d{2}$/.test(i.text));if(!prices.length)continue
  const cols:number[]=[];for(const i of [...prices].sort((a,b)=>a.x-b.x)){if(!cols.some(c=>Math.abs(c-i.x)<45))cols.push(i.x)}
  for(let ci=0;ci<cols.length;ci++){
   const x0=cols[ci]-25,x1=(cols[ci+1]??page.view[2]+25)-25;const anchors=prices.filter(i=>Math.abs(i.x-cols[ci])<45).sort((a,b)=>a.y-b.y)
   for(let k=0;k<anchors.length;k++){
    const a=anchors[k];const margin=a.size>45?145:66;const y0=a.y-margin,y1=anchors[k+1]?anchors[k+1].y-(anchors[k+1].size>45?145:66):page.view[3]-25
    const group=items.filter(i=>i.x>=x0&&i.x<x1&&i.y>=y0&&i.y<y1&&i.size<22&&i.y>50)
    const raw=group.sort((a,b)=>a.y-b.y||a.x-b.x).map(i=>i.text).join(' ').replace(/\s+/g,' ').trim()
    const name=group.filter(i=>i.size>=8&&i.size<16&&!/^(SCONTO|DA |AL |€|\d|%)/.test(i.text)).map(i=>i.text).join(' ').trim()
    if(!name||raw.length<8){warnings.push(`Pagina ${p}: prezzo ${a.text} senza descrizione leggibile, escluso.`);continue}
    offers.push({id:`p${p}-x${Math.round(a.x)}-y${Math.round(a.y)}`,page:p,price:Number(a.text.replace(',','.')),rawText:raw,name,condition,productId:'',formatIds:[],status:'candidate'})
   }
  }
 }
 matchOffers(offers)
 await doc.destroy();if(textItems<100||offers.length<10)throw Error('Testo o impaginazione del PDF non riconosciuti: nessun avviso generato.')
 return {pages:doc.numPages,textItems,offers,warnings}
}

export function matchOffers(offers:ExtractedOffer[]){
 for(const o of offers){const raw=normalize(o.rawText);const ts=new Set(raw.split(' '));const candidates=rules.filter(r=>r.tokens.every(t=>ts.has(t))&&(' '+raw+' ').includes(' '+normalize(r.quantity)+' '));if(candidates.length===1&&o.rawText.length<450){const r=candidates[0],p=products.find(p=>p.id===r.productId);if(p&&r.formatIds.every(id=>p.formats.some(f=>f.id===id))){o.productId=r.productId;o.formatIds=r.formatIds;o.status='matched'}}}
 return offers
}

export function notificationsFromExtraction(extraction:Extraction,saved:Saved[]){return extraction.offers.filter(o=>o.status==='matched'&&saved.some(s=>s.productId===o.productId&&(s.formatId==='linea'||o.formatIds.includes(s.formatId))))}
