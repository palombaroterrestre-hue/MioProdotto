import data from './catalog-data.json'
export type Format = { id: string; label: string; offerIds: string[] }
export type Offer = { id: string; price: number; starting: boolean; priceUnit: string; promo: string; flyer: number; page: number; source: string; caption: string; image: string }
export type Product = { id: string; name: string; brand: string; summary: string; facts: string[]; formats: Format[]; offers: Offer[]; image: string; imageNote: string; assortment: boolean }
export const products: Product[] = data
export type Saved = { productId: string; formatId: string }
export const STORAGE_KEY = 'mioprodotto.catalog.watchlist.v1'
export function same(a: Saved,b: Saved){ return a.productId === b.productId && a.formatId === b.formatId }
export function readSaved(raw: string | null): Saved[] {
 if(!raw) return []
 const value: unknown=JSON.parse(raw)
 if(!Array.isArray(value)) throw new Error('Invalid saved list')
 const clean: Saved[]=[]
 for(const item of value){
  if(!item || typeof item !== 'object') continue
  const c=item as Saved,p=products.find(p=>p.id===c.productId)
  if(p?.formats.some(f=>f.id===c.formatId) && !clean.some(x=>same(x,c))) clean.push({productId:c.productId,formatId:c.formatId})
 }
 return clean
}
