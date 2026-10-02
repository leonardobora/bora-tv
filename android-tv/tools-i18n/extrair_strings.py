#!/usr/bin/env python3
"""Extrai as strings de UI hard-coded do port Android TV do IPTVnator.

Por que existe: o port tem ~4.500 literais Kotlin, dos quais ~600 sao texto de
interface em espanhol. Externalizar isso a mao, em 27 arquivos, e onde o refactor
quebra. Este script faz o levantamento reproduzivel e gera o catalogo que vira
res/values/strings.xml (PT-BR) + res/values-es/strings.xml (espanhol preservado).

Saida:
  catalogo.json  - uma entrada por string: es, template com marcadores {1}..{n},
                   expressoes interpoladas, arquivos:linhas, se e composable, tipo de chave
  revisao.tsv    - para revisao humana: arquivo, linha, string
  resumo.txt     - contagens por arquivo e por categoria

Uso:
  python3 extrair_strings.py <raiz app/src/main> <dir de saida>
"""
import json, os, re, sys, collections

SPAN = re.compile(r"[áéíóúüñÁÉÍÓÚÑ¿¡]")
ES_WORDS = set("""
el la los las una un unos unas de del para por con sin y o u que se su sus tus tu
es son esta estan están este esta esto ese esa eso no si más mas menos muy ya
buscar buscar añadir anadir agregar quitar eliminar borrar editar guardar cancelar
cerrar abrir cargar conectar desconectar contraseña contrasena usuario servidor
canales canal favoritos recientes inicio ajustes ajuste fuentes fuente archivo
dispositivo credenciales portal texto deteccion detección pega opciones avanzadas
nombre nombres playlists playlist descargar descarga sincronizar restaurar backup
seleccionar selecciona seleccione introduce introduce los datos proveedor
todos todas todo toda hora horas minutos segundos hoy ayer mañana manana siguiente
anterior atras atrás arriba abajo dentro fuera listo error aviso espera cargando
reproduccion reproducción reproducir pausa detener siguiente canal volumen
programa programas guia guía pelicula película películas serie series temporada
episodio episodios calidad idioma subtitulo subtítulos audio video vídeo
hacia desde entre sobre bajo hasta cuando mientras nunca siempre solo sólo
ha has han he hemos puede pueden debe deben falta faltan quedan
""".split())

NON_UI = re.compile(
    r"^(?:[a-z0-9_]+\.)*[a-z0-9_]+$"        # chaves tipo snake/camel sem espaco
    r"|^[A-Z_]{2,}$"                          # CONSTANTES
    r"|^[\w.-]+@[\w.-]+$"
    r"|^(?:https?|rtmp|rtsp|udp|file|content|data|android)://"
    r"|^[\d\s.,:/-]+$"                        # datas, numeros, formatos
    r"|^(?:application|video|audio|text|multipart)/"
    r"|%[0-9$]*[sdf]"
    r"|^\W*\w*\.(?:json|xml|m3u8?|ts|srt|vtt|jpg|png|txt)$"
    r"|^\\\\|^/\w"
)


def scan_strings(src):
    """Devolve [(linha, texto_bruto, inicio, fim)] tratando strings Kotlin com ${...} aninhado.
    inicio/fim sao offsets de caractere do literal, incluindo as aspas."""
    out, i, n, line = [], 0, len(src), 1
    while i < n:
        c = src[i]
        if c == "\n":
            line += 1; i += 1; continue
        if c == "/" and i + 1 < n and src[i+1] == "/":
            j = src.find("\n", i); i = n if j < 0 else j; continue
        if c == "/" and i + 1 < n and src[i+1] == "*":
            j = src.find("*/", i + 2); line += src.count("\n", i, j); i = j + 2 if j > 0 else n; continue
        if c != '"':
            i += 1; continue
        start_off = i
        start_line, buf, depth, i = line, [], 0, i + 1
        while i < n:
            ch = src[i]
            if ch == "\\":
                buf.append(src[i:i+2]); i += 2; continue
            if ch == "\n":
                line += 1
            if depth == 0 and ch == '"':
                i += 1; break
            if ch == "$" and i + 1 < n and src[i+1] == "{":
                depth += 1; buf.append("${"); i += 2; continue
            if depth > 0:
                if ch == "}":
                    depth -= 1; buf.append("}"); i += 1; continue
                if ch == '"':  # string aninhada dentro do template
                    buf.append('"'); i += 1
                    d2 = 0
                    while i < n:
                        c2 = src[i]
                        if c2 == "\\": buf.append(src[i:i+2]); i += 2; continue
                        if d2 == 0 and c2 == '"': buf.append('"'); i += 1; break
                        if c2 == "$" and i + 1 < n and src[i+1] == "{": d2 += 1
                        if c2 == "}": d2 -= 1
                        buf.append(c2); i += 1
                    continue
            buf.append(ch); i += 1
        out.append((start_line, "".join(buf), start_off, i))
    return out


TEMPLATE = re.compile(r"(?<!\\)\$\{(.*?)\}|(?<!\\)\$([A-Za-z_][\w.]*)", re.S)


def to_template(raw):
    """'No se pudo: ${it.message}' -> ('No se pudo: {1}', ['it.message'])
    Trata tambem o template sem chaves: 'Bajando $progress' -> ('Bajando {1}', ['progress'])."""
    exprs = []
    def rep(m):
        exprs.append((m.group(1) or m.group(2)).strip())
        return "{%d}" % len(exprs)
    return TEMPLATE.sub(rep, raw), exprs


def is_ui_candidate(raw, tmpl):
    if len(raw.strip()) < 2:
        return False
    if NON_UI.search(raw.strip()) and not SPAN.search(raw):
        return False
    words = set(re.findall(r"[a-záéíóúüñ]+", raw.lower()))
    if SPAN.search(tmpl):
        return True
    if len(words & ES_WORDS) >= 1:
        return True
    # frase longa com espaco e maiuscula inicial: provavel texto de UI
    if " " in raw and len(raw) > 12 and raw.strip()[0].isupper():
        return len(words & ES_WORDS) >= 1
    return False


def main(root, outdir):
    os.makedirs(outdir, exist_ok=True)
    files = [os.path.join(dp, f) for dp, _, fn in os.walk(root)
             for f in fn if f.endswith(".kt")]
    entries = collections.OrderedDict()
    for p in sorted(files):
        src = open(p, encoding="utf-8", errors="ignore").read()
        if not re.search(r"@Composable", src):
            pass  # o mecanismo de tradução difere, mas a string conta igual
        for line, raw in scan_strings(src):
            tmpl, exprs = to_template(raw)
            if not is_ui_candidate(raw, tmpl):
                continue
            rel = os.path.relpath(p, root)
            e = entries.setdefault(tmpl, {"es": raw, "template": tmpl,
                                          "exprs": exprs, "sites": []})
            e["sites"].append({"file": rel, "line": line, "raw": raw})
            if exprs and not e["exprs"]:
                e["exprs"] = exprs

    arr = list(entries.values())
    for e in arr:
        e["occurrences"] = len(e["sites"])
        e["composable_file"] = any(
            "@Composable" in open(os.path.join(root, s["file"]), encoding="utf-8",
                                  errors="ignore").read() for s in e["sites"][:1])
    json.dump(arr, open(os.path.join(outdir, "catalogo.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)

    with open(os.path.join(outdir, "revisao.tsv"), "w", encoding="utf-8") as fh:
        fh.write("arquivo\tlinha\tocorrencias\tinterpolada\tstring\n")
        for e in arr:
            for s in e["sites"]:
                fh.write(f"{s['file']}\t{s['line']}\t{e['occurrences']}\t"
                         f"{'sim' if e['exprs'] else 'nao'}\t{s['raw']}\n")

    by_file = collections.Counter()
    for e in arr:
        for s in e["sites"]:
            by_file[s["file"]] += 1
    interp = sum(1 for e in arr if e["exprs"])
    with open(os.path.join(outdir, "resumo.txt"), "w", encoding="utf-8") as fh:
        fh.write(f"arquivos .kt varridos:        {len(files)}\n")
        fh.write(f"strings unicas de UI:         {len(arr)}\n")
        fh.write(f"ocorrencias no codigo:        {sum(by_file.values())}\n")
        fh.write(f"com interpolacao ${{...}}:     {interp}\n")
        fh.write(f"arquivos afetados:            {len(by_file)}\n\n")
        for f, c in by_file.most_common():
            fh.write(f"{c:5}  {f}\n")
    print(open(os.path.join(outdir, "resumo.txt"), encoding="utf-8").read())


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
