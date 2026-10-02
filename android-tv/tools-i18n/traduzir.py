#!/usr/bin/env python3
"""Gera res/values/strings.xml (PT-BR) + res/values-es/strings.xml e religa os
call sites do port Android TV do IPTVnator.

Principio de seguranca: SO e reescrito o que estiver no arquivo de traducao
(traducao.json) E for um sitio classificado como de exibicao (display). Literal
usado como chave, comparacao de logica, nome persistido ou parametro de API nao
e tocado - traduzir isso quebraria dados do usuario (ex.: o nome "Local playlist"
que vira registro no banco).

Uso:
  python3 traduzir.py --raiz <app/src/main> --i18n <dir com traducao.json> \\
      [--aplicar] [--relatorio <arquivo>]
Sem --aplicar faz apenas dry-run: mostra o que mudaria e o que foi recusado.
"""
import argparse, json, os, re, sys, unicodedata, collections

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from extrair_strings import scan_strings, to_template, is_ui_candidate  # noqa: E402

# Mensagens de interface que sao em ingles e por isso escapam do heurístico
# "parece espanhol" do extrator, mas sao visiveis para o usuario.
FORCAR = {
    "Xtream import cancelled", "Stalker account is blocked", "Unnamed",
    "Local playlist", "Xtream playlist", "Stalker portal", "Radio playlist",
}

# Strings que sao deste fork (nao existem no port original) e por isso nao passam
# pelo extrator: entram direto nos dois XML, sempre no mesmo nome de chave.
MANUAIS = {
    "sobre_titulo": {
        "pt": "Bora TV",
        "es": "Bora TV",
    },
    "sobre_autor": {
        "pt": "Adaptado e mantido por Leonardo Bora · github.com/leonardobora",
        "es": "Adaptado y mantenido por Leonardo Bora · github.com/leonardobora",
    },
    "sobre_base": {
        "pt": "Baseado no IPTVnator (MIT, © 4gray) e na porta android-tv do PR #1699.",
        "es": "Basado en IPTVnator (MIT, © 4gray) y en el port android-tv del PR #1699.",
    },
    "sobre_licenca": {
        "pt": "Build não oficial. Player apenas: não inclui canais, playlists nem assinaturas. "
              "O código de android-tv/ está sob GPL-3.0-or-later.",
        "es": "Build no oficial. Solo reproductor: no incluye canales, listas ni suscripciones. "
              "El codigo de android-tv/ esta bajo GPL-3.0-or-later.",
    },
}

# ---- classificacao -----------------------------------------------------------
# Um literal so e reescrito quando a posicao dele e de exibicao. A decisao olha
# a vizinhanca imediata do literal (±40 chars), nao a linha inteira: numa linha
# como Text(if (a != b) "Importando…" else "Cancelar") o "!=" nao diz nada sobre
# o literal, mas um "==" colado nele diz tudo.
COMPARA = re.compile(
    r"(==|!=|\.equals\(|\.equalsIgnoreCase\(|\.startsWith\(|\.endsWith\(|"
    r"\.contains\(|\.compareTo\()\s*$")
CHAVE = re.compile(
    r"(?:mapOf|mutableMapOf|setOf|hashSetOf|put|putExtra|putString|remove|"
    r"containsKey|getString|getInt|getBoolean|getLong|getOrDefault|"
    r"associateBy|groupBy|indexOf)\s*\(\s*$")
BRANCH = re.compile(r"^\s*->")
PARAM_DENY = {
    "key", "id", "tag", "type", "column", "pref", "extra", "path", "url",
    "uri", "scheme", "mime", "action", "event", "field", "param", "query",
    "providerid", "playlistid", "itemkey", "sortkey", "categorykey",
}
PARAM_OK = re.compile(
    r"\b(?:label|placeholder|contentDescription|supportingText|title|subtitle|"
    r"heading|message|confirmText|dismissText|hint|errorText|caption|description|"
    r"body|actionLabel|emptyTitle|emptyDescription|emptyActionLabel|emptyText|"
    r"tooltip|statusText|labelText|text|value)\s*=\s*$")
CHAMADA = re.compile(r"[A-Z]\w*\s*\(\s*$")          # chamada/construtor capitalizado (Compose)


def classificar(src, s0, s1):
    """Devolve (ok, motivo). ok=True apenas para posicao de exibicao."""
    b40 = src[max(0, s0 - 40): s0]
    a40 = src[s1: s1 + 40]
    if BRANCH.match(a40):
        return False, "rotulo de branch (when/case)"
    if COMPARA.search(b40) or re.match(r"\s*(==|!=|\.equals\()", a40):
        return False, "literal comparado (chave de logica)"
    if CHAVE.search(b40):
        return False, "chave de mapa/preferencia/extra"
    m = re.search(r"([A-Za-z_][\w]*)\s*=\s*$", b40)
    if m and m.group(1).lower() in PARAM_DENY:
        return False, f"parametro de dado ({m.group(1)})"
    if PARAM_OK.search(b40):
        return True, "parametro de exibicao"
    # Posicao de argumento: `Foo("texto")`, `Foo(1, "texto")`, `MINHA_LISTA("texto")`.
    # E onde vivem os rotulos de enum e os argumentos posicionais de UI - a maior
    # parte do menu lateral, por exemplo.
    if re.search(r"[,({]\s*$", b40):
        return True, "posicao de argumento"
    # Valor de um branch de `when`: `"chave" -> "texto mostrado"`. O rotulo do
    # branch ja foi recusado acima (literal seguido de ->), este e o resultado.
    if re.search(r"->\s*$", b40):
        return True, "valor de branch"
    # Atribuicao simples: `val titulo = "texto"` (parametro de dado ja foi recusado acima).
    if re.search(r"[^=!<>+\-*/%&|^]=\s*$", b40):
        return True, "atribuicao"
    if re.search(r"(Text|BasicText)\s*\(\s*$", b40):
        return True, "Text(...)"
    if re.search(r"(\?:|\|\||&&|\{)\s*$", b40):
        return True, "fallback/bloco"
    return False, "posicao nao reconhecida"


# ---- chaves ------------------------------------------------------------------
def slug(pt: str) -> str:
    t = unicodedata.normalize("NFKD", pt).encode("ascii", "ignore").decode()
    t = re.sub(r"\{[0-9]+\}|%[0-9]*\$?[sd]", " ", t)
    t = re.sub(r"[^a-zA-Z0-9]+", "_", t).strip("_").lower()
    t = re.sub(r"_+", "_", t)[:44].strip("_")
    if not t:
        t = "texto"
    if t[0].isdigit():
        t = "n_" + t
    return t


def unescape_kotlin(s: str) -> str:
    out, i = [], 0
    while i < len(s):
        c = s[i]
        if c == "\\" and i + 1 < len(s):
            n = s[i + 1]
            out.append({"n": "\n", "t": "\t", "r": "\r", '"': '"', "'": "'",
                        "\\": "\\", "$": "$"}.get(n, "\\" + n))
            i += 2
        else:
            out.append(c); i += 1
    return "".join(out)


def xml_escape(s: str, has_args: bool) -> str:
    s = s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    s = s.replace("'", "\\'").replace('"', '\\"')
    if has_args:
        # primeiro neutraliza % literal, depois converte os marcadores {n} para a
        # sintaxe que o getString(id, args) entende. Sem isso a tela mostraria "{1}".
        s = s.replace("%", "%%")
        s = re.sub(r"\{(\d+)\}", lambda m: "%" + m.group(1) + "$s", s)
    # newline literal dentro de strings.xml vira \n
    return s.replace("\n", "\\n")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--raiz", required=True)
    ap.add_argument("--i18n", required=True)
    ap.add_argument("--aplicar", action="store_true")
    ap.add_argument("--relatorio", default=None)
    ap.add_argument("--pendentes", default=None,
                    help="grava JSON com as strings de UI que ainda nao tem traducao")
    a = ap.parse_args()

    tradu = json.load(open(os.path.join(a.i18n, "traducao.json"), encoding="utf-8"))
    # chave do map = texto ES ja desescapado (o que o usuario ve)
    traduc = {unescape_kotlin(k) if "\\" in k else k: v for k, v in tradu.items()}

    files = [os.path.join(dp, f) for dp, _, fn in os.walk(a.raiz)
             for f in fn if f.endswith(".kt")]
    keys, used = {}, {}          # es -> key ; key -> es
    entradas = {}                # es -> {"pt":..., "es":..., "exprs":[...]}
    rewrites, recusados, ignorados = [], [], []
    pendentes = {}

    def chave_de(es, pt):
        k = keys.get(es)
        if k is None:
            base, k, n = slug(pt), slug(pt), 2
            while k in used and used[k] != es:
                k = f"{base}_{n}"; n += 1
            keys[es] = k
            used[k] = es
        return k

    # Semeia o catalogo com o mapa de traducao inteiro. Sem isso o gerador so
    # emitiria strings que ainda tem literal no fonte - e depois de um --aplicar
    # elas ja viraram str(R.string.x), entao o XML sairia vazio e o build quebraria.
    for es, pt in traduc.items():
        if not es or es.startswith("_") or not pt:
            continue
        marcadores = len(re.findall(r"\{\d+\}", es))
        entradas[es] = {"pt": pt, "es": es, "exprs": [""] * marcadores}
        chave_de(es, pt)

    for p in sorted(files):
        src = open(p, encoding="utf-8", errors="ignore").read()
        rel = os.path.relpath(p, a.raiz)
        for line, raw, s0, s1 in scan_strings(src):
            tmpl_src, exprs = to_template(raw)
            visivel = unescape_kotlin(raw)
            visivel_tmpl = unescape_kotlin(tmpl_src)
            # dois crivos: (1) o literal PARECE texto de interface, (2) a posicao
            # dele e de exibicao. Sem o primeiro, SQL e nomes de coluna entram.
            if not is_ui_candidate(raw, visivel_tmpl) and visivel_tmpl not in FORCAR:
                ignorados.append((rel, line, raw, "nao parece texto de UI"))
                continue
            ok, motivo = classificar(src, s0, s1)
            if not ok:
                recusados.append((rel, line, raw, motivo))
                continue
            pt = traduc.get(visivel_tmpl) or traduc.get(visivel)
            if not pt:
                pend = pendentes.setdefault(visivel_tmpl,
                                            {"es": visivel_tmpl, "exprs": exprs, "sites": 0})
                pend["sites"] += 1
                ignorados.append((rel, line, raw, "falta traducao"))
                continue
            nmarc = len(re.findall(r"\{\d+\}", pt))
            if nmarc != len(exprs):
                recusados.append((rel, line, raw,
                                  f"marcadores ({nmarc}) != expressoes ({len(exprs)})"))
                continue
            k = keys.get(visivel_tmpl)
            if k is None:
                k = chave_de(visivel_tmpl, pt)
            entradas.setdefault(visivel_tmpl, {"pt": pt, "es": visivel_tmpl, "exprs": exprs})
            if exprs:
                expr_kotlin = ", " + ", ".join(exprs)
            else:
                expr_kotlin = ""
            novo = f"str(R.string.{k}{expr_kotlin})"
            rewrites.append((p, rel, s0, s1, raw, novo, line, visivel))

    # ---- aplica (de tras para frente para nao invalidar offsets) ----
    por_arquivo = collections.defaultdict(list)
    for r in rewrites:
        por_arquivo[r[0]].append(r)
    for p, lista in por_arquivo.items():
        src = open(p, encoding="utf-8", errors="ignore").read()
        for (_, rel, s0, s1, raw, novo, line, visivel) in sorted(lista, key=lambda x: -x[2]):
            src = src[:s0] + novo + src[s1:]
        m = re.search(r"^package\s+([\w.]+)", src, re.M)
        imports = []
        if m and "import com.iptvnator.googletv.R\n" not in src and m.group(1) != "com.iptvnator.googletv":
            imports.append("import com.iptvnator.googletv.R")
        if m and "import com.iptvnator.googletv.str\n" not in src and m.group(1) != "com.iptvnator.googletv":
            imports.append("import com.iptvnator.googletv.str")
        if imports:
            m = list(re.finditer(r"^(import .+|package .+)$", src, re.M))[-1]
            src = src[:m.end()] + "\n" + "\n".join(imports) + src[m.end():]
        if a.aplicar:
            open(p, "w", encoding="utf-8").write(src)

    # ---- recursos ----
    os.makedirs(os.path.join(a.raiz, "res/values"), exist_ok=True)
    os.makedirs(os.path.join(a.raiz, "res/values-es"), exist_ok=True)
    for pasta, campo, cab in (("values", "pt", "PT-BR (padrao)"),
                              ("values-es", "es", "Espanhol (original)")):
        linhas = ['<?xml version="1.0" encoding="utf-8"?>',
                  f"<!-- {cab} - gerado por tools-i18n/traduzir.py -->",
                  "<resources>"]
        for es, d in sorted(entradas.items(), key=lambda kv: keys[kv[0]]):
            args = bool(d["exprs"])
            linhas.append(f'    <!-- ES: {xml_escape(d["es"], False)} -->')
            linhas.append(f'    <string name="{keys[es]}">'
                          f'{xml_escape(d[campo], args)}</string>')
        for nome, vals in MANUAIS.items():
            linhas.append(f'    <string name="{nome}">{xml_escape(vals[campo], False)}</string>')
        linhas.append("</resources>")
        destino = os.path.join(a.raiz, "res", pasta, "strings.xml")
        if a.aplicar:
            open(destino, "w", encoding="utf-8").write("\n".join(linhas) + "\n")
        print(f"{'gravado' if a.aplicar else 'seria gravado'}: {destino} "
              f"({len(entradas)} strings)")

    print(f"\nsites reescritos:  {len(rewrites)}")
    print(f"sites recusados:   {len(recusados)}")
    print(f"sites sem traducao:{len(ignorados)}")
    print(f"strings no catalogo: {len(entradas)}")
    print(f"strings de UI pendentes de traducao: {len(pendentes)} "
          f"({sum(p['sites'] for p in pendentes.values())} sites)")
    if a.pendentes:
        json.dump(sorted(pendentes.values(), key=lambda p: -p["sites"]),
                  open(a.pendentes, "w", encoding="utf-8"),
                  ensure_ascii=False, indent=1)
        print(f"pendentes > {a.pendentes}")
    if a.relatorio:
        with open(a.relatorio, "w", encoding="utf-8") as fh:
            fh.write("== REESCRITOS ==\n")
            for _, rel, _, _, raw, novo, line, _v in rewrites:
                fh.write(f"{rel}:{line}\n   - {raw}\n   + {novo}\n")
            fh.write("\n== RECUSADOS ==\n")
            for rel, line, raw, motivo in recusados:
                fh.write(f"{rel}:{line} [{motivo}] {raw}\n")
        print(f"relatorio: {a.relatorio}")


if __name__ == "__main__":
    main()
