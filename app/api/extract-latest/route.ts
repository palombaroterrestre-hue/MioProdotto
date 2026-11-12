import {latestExtraction} from '../../../lib/live-extraction'
export const runtime='nodejs'
export const dynamic='force-dynamic'
export const maxDuration=60
export async function POST(request:Request){
 const origin=request.headers.get('origin'),host=request.headers.get('x-forwarded-host')||request.headers.get('host');if(request.headers.get('sec-fetch-site')==='cross-site'||(origin&&host&&new URL(origin).host!==host))return Response.json({error:'Origine richiesta non valida.'},{status:403})
 try{const result=await latestExtraction();return Response.json(result,{headers:{'Cache-Control':'no-store'}})}catch(e){return Response.json({error:e instanceof Error?e.message:'Estrazione fallita. Nessun dato precedente utilizzato.'},{status:502,headers:{'Cache-Control':'no-store'}})}
}
