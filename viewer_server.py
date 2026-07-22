import http.server
import socketserver

PORT = 3000
DIRECTORY = "outputs"

class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)
        
    def do_GET(self):
        if self.path == '/':
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            
            html = """
            <!DOCTYPE html>
            <html>
            <head>
                <title>KaRar BIM Viewer</title>
                <style>
                    body { margin: 0; padding: 20px; font-family: -apple-system, sans-serif; background: #0f172a; color: #f8fafc; }
                    .header { margin-bottom: 20px; border-bottom: 1px solid #334155; padding-bottom: 10px; }
                    h1 { margin: 0; color: #38bdf8; }
                    .stats { display: flex; gap: 20px; margin-top: 10px; color: #94a3b8; }
                    .stat-item { background: #1e293b; padding: 10px 15px; border-radius: 6px; }
                    .stat-value { font-size: 1.2em; font-weight: bold; color: #fff; margin-left: 8px; }
                    canvas { background: #000; border: 1px solid #334155; border-radius: 8px; width: 100%; max-width: 1200px; height: 800px; }
                </style>
            </head>
            <body>
                <div class="header">
                    <h1>KaRar BIM Core Engine</h1>
                    <div class="stats" id="stats-container">Loading semantics...</div>
                </div>
                <canvas id="viewer" width="1200" height="800"></canvas>

                <script>
                    fetch('/bim_model.json')
                        .then(res => res.json())
                        .then(data => {
                            const meta = data.metadata;
                            document.getElementById('stats-container').innerHTML = `
                                <div class="stat-item">Spaces <span class="stat-value">${meta.total_spaces}</span></div>
                                <div class="stat-item">Walls <span class="stat-value">${meta.total_walls}</span></div>
                                <div class="stat-item">Doors <span class="stat-value">${meta.total_doors}</span></div>
                                <div class="stat-item">Windows <span class="stat-value">${meta.total_windows}</span></div>
                                <div class="stat-item">Columns <span class="stat-value">${meta.total_columns}</span></div>
                            `;
                            
                            const canvas = document.getElementById('viewer');
                            const ctx = canvas.getContext('2d');
                            
                            let minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity;
                            
                            data.elements.forEach(el => {
                                if (el.type === 'Space') {
                                    el.boundary.forEach(p => {
                                        if (p.x < minX) minX = p.x;
                                        if (p.y < minY) minY = p.y;
                                        if (p.x > maxX) maxX = p.x;
                                        if (p.y > maxY) maxY = p.y;
                                    });
                                } else if (el.geometry && el.geometry.points) {
                                    el.geometry.points.forEach(p => {
                                        if (p[0] < minX) minX = p[0];
                                        if (p[1] < minY) minY = p[1];
                                        if (p[0] > maxX) maxX = p[0];
                                        if (p[1] > maxY) maxY = p[1];
                                    });
                                }
                            });
                            
                            if (minX === Infinity) {
                                minX = 0; minY = 0; maxX = 1200; maxY = 1200;
                            }
                            
                            const padding = 50;
                            const scaleX = (canvas.width - padding*2) / (maxX - minX);
                            const scaleY = (canvas.height - padding*2) / (maxY - minY);
                            const scale = Math.min(scaleX, scaleY);
                            
                            const transformX = x => padding + (x - minX) * scale;
                            const transformY = y => canvas.height - (padding + (y - minY) * scale);
                            
                            data.elements.filter(e => e.type === 'Space').forEach(space => {
                                ctx.beginPath();
                                space.boundary.forEach((p, i) => {
                                    const tx = transformX(p.x);
                                    const ty = transformY(p.y);
                                    if (i === 0) ctx.moveTo(tx, ty);
                                    else ctx.lineTo(tx, ty);
                                });
                                ctx.closePath();
                                ctx.fillStyle = 'rgba(56, 189, 248, 0.1)';
                                ctx.fill();
                                ctx.strokeStyle = 'rgba(56, 189, 248, 0.3)';
                                ctx.lineWidth = 1;
                                ctx.stroke();
                            });
                            
                            data.elements.filter(e => e.type !== 'Space').forEach(el => {
                                if (!el.geometry || !el.geometry.points) return;
                                ctx.beginPath();
                                el.geometry.points.forEach((p, i) => {
                                    const tx = transformX(p[0]);
                                    const ty = transformY(p[1]);
                                    if (i === 0) ctx.moveTo(tx, ty);
                                    else ctx.lineTo(tx, ty);
                                });
                                
                                ctx.lineWidth = 2;
                                if (el.type === 'Wall') {
                                    ctx.strokeStyle = '#94a3b8';
                                } else if (el.type === 'Column') {
                                    ctx.strokeStyle = '#f87171';
                                    ctx.lineWidth = 3;
                                } else if (el.type === 'Door') {
                                    ctx.strokeStyle = '#4ade80';
                                    ctx.lineWidth = 2;
                                } else if (el.type === 'Window') {
                                    ctx.strokeStyle = '#60a5fa';
                                    ctx.lineWidth = 2;
                                }
                                ctx.stroke();
                            });
                        })
                        .catch(err => {
                            document.getElementById('stats-container').innerHTML = `Error loading BIM model: ${err}`;
                        });
                </script>
            </body>
            </html>
            """
            self.wfile.write(html.encode('utf-8'))
        else:
            super().do_GET()

with socketserver.TCPServer(("0.0.0.0", PORT), Handler) as httpd:
    print(f"Serving at port {PORT}")
    httpd.serve_forever()
