/** @type {import('next').NextConfig} */
const nextConfig = {
 serverExternalPackages: ['pdfjs-dist'],
 outputFileTracingIncludes: {'/api/extract-latest':['./node_modules/pdfjs-dist/legacy/build/pdf.worker.mjs']}
}
module.exports = nextConfig
