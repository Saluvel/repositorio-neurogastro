#!/usr/bin/env python3
"""Genera una copia offline del sitio en UN solo archivo HTML.

Uso (desde la raíz del repositorio):
    python3 herramientas/generar_offline.py            # crea repositorio-de-moises-offline.html
    python3 herramientas/generar_offline.py salida.html

Cómo funciona: cada página del sitio se guarda como texto dentro del archivo final.
Una pequeña "carcasa" muestra la página elegida en un marco (iframe) y atrapa los
clics en enlaces internos para cambiar de página sin necesitar internet ni GitHub.
"""
import base64, json, pathlib, re, sys

RAIZ = pathlib.Path(__file__).resolve().parent.parent
PAGINAS = ["index.html", "guia-2026.html", "quiz/index.html", "fenotipos/index.html",
           "estudios/index.html", "calc/index.html", "atlas/index.html", "pacientes/index.html"]

icono = "data:image/png;base64," + base64.b64encode((RAIZ / "icons/icon-192.png").read_bytes()).decode()

# Script que se inyecta en cada página: intercepta enlaces internos y externos.
PUENTE = """<base href="about:srcdoc"><script>(function(){var V=%s;
function go(a,e){var h=a.getAttribute('href');if(!h||h.charAt(0)==='#'||/^(javascript|mailto|tel|blob|data):/i.test(h))return;
var u;try{u=new URL(h,'https://sitio.local/'+V)}catch(x){return}
if(u.host!=='sitio.local'){if(a.target!=='_blank'){e.preventDefault();window.open(u.href,'_blank','noopener')}return}
e.preventDefault();var p=u.pathname.replace(/^\\//,'');if(p===''||/\\/$/.test(p))p+='index.html';
parent.postMessage({ngIr:p,hash:u.hash},'*')}
document.addEventListener('click',function(e){if(e.defaultPrevented||e.button!==0||e.metaKey||e.ctrlKey)return;var a=e.target.closest&&e.target.closest('a[href]');if(a&&!a.hasAttribute('download'))go(a,e)},true);
})();</script>"""

def preparar(ruta):
    html = (RAIZ / ruta).read_text(encoding="utf-8")
    # Quitar manifest/íconos (no aplican offline) y poner el ícono incrustado.
    html = re.sub(r'<link[^>]+rel="(manifest|icon|apple-touch-icon)"[^>]*>\s*', "", html)
    html = re.sub(r"(<head[^>]*>)", lambda m: m.group(1) + PUENTE % json.dumps(ruta), html, count=1)
    # El quiz cree que está "incrustado" al verse dentro del marco y desactiva las
    # descargas; aquí sí se puede descargar normalmente.
    html = html.replace("return window.self!==window.top", "return false")
    return html

datos = {p: preparar(p) for p in PAGINAS}
titulo = re.search(r"<title>(.*?)</title>", datos["index.html"], re.S)
titulo = titulo.group(1).strip() if titulo else "Repositorio de Moisés"
json_paginas = json.dumps(datos, ensure_ascii=False).replace("</", "<\\/")

CARCASA = f"""<!doctype html>
<html lang="es"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{titulo} (offline)</title>
<link rel="icon" type="image/png" href="{icono}">
<style>html,body{{margin:0;height:100%;background:#fff}}iframe{{border:0;width:100%;height:100%;display:block}}</style>
</head><body>
<iframe id="marco" title="{titulo}"></iframe>
<script id="paginas" type="application/json">{json_paginas}</script>
<script>
var P=JSON.parse(document.getElementById('paginas').textContent),M=document.getElementById('marco'),actual=null;
function leer(){{var h=decodeURIComponent(location.hash.slice(1)),i=h.indexOf('#');return{{p:(i<0?h:h.slice(0,i))||'index.html',a:i<0?'':h.slice(i)}}}}
function mostrar(){{var r=leer();if(!P[r.p])r={{p:'index.html',a:''}};
 if(r.p!==actual){{actual=r.p;M.srcdoc=P[r.p];M.onload=function(){{try{{document.title=M.contentDocument.title||document.title;if(r.a){{var el=M.contentDocument.getElementById(r.a.slice(1));if(el)el.scrollIntoView();else M.contentWindow.location.hash=r.a}}}}catch(e){{}}}}}}
 else if(r.a){{try{{var el=M.contentDocument.getElementById(r.a.slice(1));if(el)el.scrollIntoView();else M.contentWindow.location.hash=r.a}}catch(e){{}}}}}}
addEventListener('message',function(e){{var d=e.data;if(d&&d.ngIr&&P[d.ngIr]){{var n='#'+d.ngIr+(d.hash||'');if(location.hash===n)mostrar();else location.hash=n}}}});
addEventListener('hashchange',mostrar);mostrar();
</script></body></html>"""

salida = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else RAIZ / "repositorio-de-moises-offline.html"
salida.write_text(CARCASA, encoding="utf-8")
print(f"Listo: {salida} ({salida.stat().st_size/1024:.0f} KB)")
