"""
Tema de accesibilidad compartido para todas las superficies HTML de Noósfera.

Reglas (requisito del usuario):
- Modo OSCURO por defecto siempre.
- Modo claro seleccionable por el usuario (no automático).
- Texto base mínimo 18px en todas las superficies.
- Alto contraste: texto blanco sobre negro.
- Foco visible para navegación por teclado.

Uso:
    html = TEMPLATE.replace("{css_tema}", css_tema())
"""

from __future__ import annotations

# Mínimo de tamaño de texto aceptable en cualquier superficie.
# Por debajo de esto se considera fallo de accesibilidad.
MIN_FUENTE_PX = 18

# Modo por defecto: oscuro. El claro solo se activa si el usuario lo elige.
MODO_POR_DEFECTO = "oscuro"


def css_tema(modo: str = MODO_POR_DEFECTO) -> str:
    """CSS de variables de tema. `modo` es 'oscuro' o 'claro'.

    El modo por defecto es oscuro. El claro se selecciona explícitamente.
    """
    if modo == "claro":
        vars_css = (
            ":root{--bg:#ffffff;--panel:#f4f4f4;--text:#111111;"
            "--muted:#333333;--accent:#8a5a00;--border:#666666;--focus:#0b57d0;}"
        )
    else:
        vars_css = (
            ":root{--bg:#000000;--panel:#0b0b0b;--text:#ffffff;"
            "--muted:#dcdcdc;--accent:#ffd54a;--border:#3a3a3a;--focus:#ffd54a;}"
        )

    return f"""{vars_css}
  *{{box-sizing:border-box}}
  html{{font-size:{MIN_FUENTE_PX}px}}
  html,body{{margin:0;background:var(--bg);color:var(--text);
    font-family:system-ui,-apple-system,Segoe UI,Roboto,Ubuntu,Cantarell,Noto Sans,sans-serif;
    line-height:1.7}}
  a{{color:#9ecbff}}
  a:focus,button:focus,[tabindex]:focus{{outline:3px solid var(--focus);outline-offset:2px}}
  .meta,.row,.chip,.link,.pred,.footer,.role{{font-size:{MIN_FUENTE_PX}px}}
  h1{{font-size:32px}} h2{{font-size:24px}}"""


# JS mínimo para que el usuario pueda conmutar tema. Se guarda la elección
# en localStorage para que persista entre visitas.
CONMUTADOR_JS = """
(function(){
  var b=document.createElement('button');
  b.textContent='Cambiar tema';
  b.style.cssText='position:fixed;top:8px;right:8px;z-index:99;padding:10px 16px;'
    +'font-size:18px;cursor:pointer;background:var(--panel);color:var(--text);'
    +'border:2px solid var(--border);border-radius:8px';
  b.onclick=function(){
    var claro=document.documentElement.classList.toggle('tema-claro');
    try{localStorage.setItem('noosfera_tema', claro?'claro':'oscuro')}catch(e){}
  };
  document.body.appendChild(b);
  try{
    if(localStorage.getItem('noosfera_tema')==='claro'){
      document.documentElement.classList.add('tema-claro');
    }
  }catch(e){}
})();
"""


def conmutar_tema_js() -> str:
    """Devuelve el JS del conmutador de tema (oscuro por defecto)."""
    return CONMUTADOR_JS
