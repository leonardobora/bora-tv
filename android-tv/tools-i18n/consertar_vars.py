#!/usr/bin/env python3
"""Conserta os sites que perderam interpolacao `$var` (template sem chaves).

Contexto: o scanner original so entendia `${expr}`. Um literal como
"Duración: $it" era convertido para str(R.string.duracao_it) SEM o argumento -
a variavel sumia da mensagem. O scanner ja foi corrigido; este script:

  1. restaura no fonte o literal original daqueles sites (a partir do mapa de
     traducao, que guarda o texto ES como estava),
  2. reescreve o mapa para a forma com marcadores ({1}, {2}...) nos dois lados,
  3. deixa o traduzir.py refazer a reescrita, agora com os argumentos certos.

Uso: python3 consertar_vars.py --raiz <app/src/main> --i18n <dir> [--aplicar]
"""
import argparse, json, os, re, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from traduzir import slug                    # mesma funcao de chave
from extrair_strings import TEMPLATE          # mesma deteccao de template

BARE = re.compile(r"(?<!\\)\$([A-Za-z_][\w.]*)")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--raiz", required=True)
    ap.add_argument("--i18n", required=True)
    ap.add_argument("--aplicar", action="store_true")
    a = ap.parse_args()

    caminho = os.path.join(a.i18n, "traducao.json")
    traducao = json.load(open(caminho, encoding="utf-8"))

    alvos = {}
    for es, pt in list(traducao.items()):
        if es.startswith("_") or not pt:
            continue
        vares = BARE.findall(es)
        if vares:
            alvos[es] = (pt, vares)

    if not alvos:
        print("nada a consertar"); return
    print(f"entradas com template sem chaves: {len(alvos)}")

    files = [os.path.join(dp, f) for dp, _, fn in os.walk(a.raiz)
             for f in fn if f.endswith(".kt")]

    restaurados = 0
    for es, (pt, vares) in alvos.items():
        nome = slug(pt)
        expr = 'str(R.string.%s)' % nome
        for p in files:
            src = open(p, encoding="utf-8").read()
            if expr in src:
                n = src.count(expr)
                # devolve o literal original para o pipeline reprocessar
                src = src.replace(expr, '"%s"' % es.replace('"', '\\"'))
                open(p, "w", encoding="utf-8").write(src)
                restaurados += n
    print(f"sites restaurados no fonte: {restaurados}")

    # mapa passa a usar marcadores nos dois lados (mesma numeracao do scanner)
    from extrair_strings import to_template
    novo = {}
    for k, v in traducao.items():
        if k in alvos:
            k_novo, exprs = to_template(k)          # mesma conta que o pipeline faz
            v_novo = v
            for i, e in enumerate(exprs, 1):
                nome = e.strip()
                if not nome:
                    continue
                v_novo = re.sub(r"(?<!\\)\$\{%s\}" % re.escape(nome),
                                "{%d}" % i, v_novo)
                v_novo = re.sub(r"(?<!\\)\$%s\b" % re.escape(nome),
                                "{%d}" % i, v_novo)
            novo[k_novo] = v_novo
        else:
            novo[k] = v
    if a.aplicar:
        json.dump(novo, open(caminho, "w", encoding="utf-8"),
                  ensure_ascii=False, indent=1)
        print(f"mapa reescrito: {len(alvos)} entradas agora com marcadores")
    print("\n-- amostra --")
    for k in list(alvos)[:8]:
        kn, ex = to_template(k)
        print(f"   ES {kn!r}  (args={ex})\n   PT {novo.get(kn, '(nao casou)')!r}")


if __name__ == "__main__":
    main()
