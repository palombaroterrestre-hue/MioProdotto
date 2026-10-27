import data from './1-dedup-data.json'
import aliasData from './2-dedup-aliases.json'
import reviewRequired from './3-dedup-review-required.json'
export type Format = { id: string; label: string; offerIds: string[] }
export type Offer = { id: string; price: number; starting: boolean; priceUnit: string; promo: string; flyer: number; page: number; source: string; caption: string; image: string }
export type Product = { id: string; name: string; brand: string; summary: string; facts: string[]; formats: Format[]; offers: Offer[]; image: string; imageNote: string; assortment: boolean; sourceCaseIds: string[] }
export const products: Product[] = data
export type Saved = { productId: string; formatId: string }
const aliases: Record<string,Saved> = aliasData
export const STORAGE_KEY = 'mioprodotto.catalog.watchlist.v1'
export const BACKUP_KEY = 'mioprodotto.catalog.watchlist.before-identity-migration.v1'
export const PENDING_KEY = 'mioprodotto.catalog.watchlist.unresolved.v1'
export function same(a: Saved,b: Saved){ return a.productId === b.productId && a.formatId === b.formatId }
export function migrateSaved(raw: string | null): {saved:Saved[];unresolved:Saved[];changed:boolean} {
 if(!raw) return {saved:[],unresolved:[],changed:false}
 const value: unknown=JSON.parse(raw)
 if(!Array.isArray(value)) throw new Error('Invalid saved list')
 const saved: Saved[]=[],unresolved:Saved[]=[]
 for(const item of value){
  if(!item || typeof item !== 'object') continue
  const old=item as Saved
  if(typeof old.productId!=='string'||typeof old.formatId!=='string')continue
  const needsReview=reviewRequired.includes(old.productId+'/'+old.formatId)
  const c=aliases[old.productId+'/'+old.formatId]||old,p=needsReview?undefined:products.find(p=>p.id===c.productId)
  if(p?.formats.some(f=>f.id===c.formatId)) {if(!saved.some(x=>same(x,c))) saved.push({productId:c.productId,formatId:c.formatId})}
  else if(!unresolved.some(x=>same(x,old)))unresolved.push({productId:old.productId,formatId:old.formatId})
 }
 return {saved,unresolved,changed:JSON.stringify(saved)!==raw||unresolved.length>0}
}
export function readSaved(raw:string|null):Saved[]{return migrateSaved(raw).saved}
