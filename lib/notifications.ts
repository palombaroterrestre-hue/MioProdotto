import source from './latest-flyer.json'
import {Saved} from './catalog'
export type CurrentOffer={id:string;name:string;format:string;price:number|null;discount:string;page:number;condition:string;productId:string;formatIds:string[]}
export const demoFlyer:{title:string;region:string;validFrom:string;validTo:string;checkedAt:string;source:string;indexSource:string;offers:CurrentOffer[]}=source
export function matchingOffers(saved:Saved[]){return demoFlyer.offers.filter(o=>o.productId&&saved.some(s=>s.productId===o.productId&&(s.formatId==='linea'||o.formatIds.includes(s.formatId))))}
