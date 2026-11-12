/** @type {import('next').NextConfig} */
const nextConfig = {
 serverExternalPackages: ['pdfjs-dist','@napi-rs/canvas'],
 outputFileTracingIncludes: {'/api/extract-latest':['./node_modules/pdfjs-dist/legacy/build/pdf.worker.mjs','./node_modules/@napi-rs/canvas/**/*','./node_modules/@napi-rs/canvas-linux-x64-gnu/**/*']}
}
module.exports = nextConfig
