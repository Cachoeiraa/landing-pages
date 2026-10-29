# Gera as versoes publicas (minificadas + protegidas) a partir dos fontes em src/
# Uso: python build.py  ->  reescreve os index.html publicados
import re
from pathlib import Path

ROOT = Path(__file__).parent
SRC = ROOT / "src"

# Script de protecao (ofuscado): bloqueia F12, Ctrl+U/S, Ctrl+Shift+I/J/C/K,
# botao direito e trava inspecao quando DevTools estiver aberto
PROTECT = (
    "<script>(function(){var _0xab=['Y29udGV4dG1lbnU=','a2V5ZG93bg==','RjEy','ZGVidWdnZXI='];"
    "var _0xd=function(i){return atob(_0xab[i])};"
    "document.addEventListener(_0xd(0),function(e){e.preventDefault()});"
    "document.addEventListener(_0xd(1),function(e){var k=e.key||'';"
    "if(k===_0xd(2)||(e.ctrlKey&&e.shiftKey&&['I','J','C','K'].indexOf(k.toUpperCase())>-1)||"
    "(e.ctrlKey&&['u','s'].indexOf(k.toLowerCase())>-1))e.preventDefault()});"
    "setInterval(function(){new Function(_0xd(3))()},200)})();</script>"
)


def minify_css(css: str) -> str:
    css = re.sub(r"/\*[\s\S]*?\*/", "", css)          # remove comentarios
    css = re.sub(r"\s+", " ", css)                     # colapsa espacos
    css = re.sub(r"\s*([{}:;,>+~])\s*", r"\1", css)    # espaco em volta de simbolos
    return css.replace(";}", "}").strip()


def minify_html(text: str) -> str:
    # retira blocos <style>/<script> para nao quebrar CSS/JS
    blocks = []

    def stash(m):
        blocks.append(m.group(0))
        return f"%%BLOCK{len(blocks) - 1}%%"

    text = re.sub(r"<style[\s\S]*?</style>", stash, text)
    text = re.sub(r"<script[\s\S]*?</script>", stash, text)

    text = re.sub(r"<!--[\s\S]*?-->", "", text)        # remove comentarios HTML

    parts = re.split(r"(<[^>]+>)", text)               # separa tags de texto
    text = "".join(re.sub(r"\s+", " ", p) for p in parts)
    text = re.sub(r">\s+<", "><", text)                # espaco entre tags

    def unstash(m):
        b = blocks[int(m.group(1))]
        if b.startswith("<style"):
            open_tag = re.match(r"\s*(<style[^>]*>)", b).group(1)
            inner = re.sub(r"^\s*<style[^>]*>|</style>\s*$", "", b)
            return open_tag + minify_css(inner) + "</style>"
        return b

    text = re.sub(r"%%BLOCK(\d+)%%", unstash, text)
    text = text.replace("</body>", PROTECT + "</body>")
    return text.strip()


count = 0
for src_file in SRC.rglob("index.html"):
    target = ROOT / src_file.relative_to(SRC)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(minify_html(src_file.read_text(encoding="utf-8")), encoding="utf-8")
    count += 1

print(f"{count} pagina(s) minificadas e protegidas")
