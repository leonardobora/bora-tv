#!/usr/bin/env python3
"""Renomeia vocabulario que e ao mesmo tempo chave de dispatch e rotulo de tela.

Por que existe: em varios pontos o app guarda o texto que mostra E compara com ele
(`listOf("General", ...)` + `when (selected) { "General" -> ... }`; chips de filtro
iguais). Traduzir so o lado visivel faz o filtro parar de casar. Aqui o literal e
substituido em TODAS as ocorrencias, entao chave e rotulo mudam juntos.

Diferente de traduzir.py, este passo NAO cria recurso: o valor continua no codigo,
apenas em portugues. Uso:

  python3 renomear.py --raiz <app/src/main> --mapa <i18n/renomear.json> [--aplicar]

Sem --aplicar so relata. Com --aplicar reescreve e depois VERIFICA que nao sobrou
nenhuma ocorrencia do literal antigo (senao algum `when` continuaria em espanhol).
"""
import argparse, json, os, re, sys

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--raiz", required=True)
    ap.add_argument("--mapa", required=True)
    ap.add_argument("--aplicar", action="store_true")
    a = ap.parse_args()

    mapa = json.load(open(a.mapa, encoding="utf-8"))
    mapa = {k: v for k, v in mapa.items() if not k.startswith("_") and k != v}
    if not mapa:
        print("nada a renomear"); return

    files = [os.path.join(dp, f) for dp, _, fn in os.walk(a.raiz)
             for f in fn if f.endswith(".kt")]

    conta = {k: 0 for k in mapa}
    for p in sorted(files):
        src = open(p, encoding="utf-8").read()
        novo = src
        for es, pt in mapa.items():
            alvo = '"%s"' % es.replace('"', '\\"')
            subs = '"%s"' % pt.replace('"', '\\"')
            n = novo.count(alvo)
            if n:
                conta[es] += n
                novo = novo.replace(alvo, subs)
        if novo != src and a.aplicar:
            open(p, "w", encoding="utf-8").write(novo)

    print(f"{'renomeado' if a.aplicar else 'seria renomeado'}:")
    for es, n in sorted(conta.items(), key=lambda kv: -kv[1]):
        if n:
            print(f"   {n:3}x  {es!r} -> {mapa[es]!r}")

    # verificacao: nenhum literal antigo pode sobrar
    sobras = {}
    for p in sorted(files):
        src = open(p, encoding="utf-8").read()
        for es in mapa:
            alvo = '"%s"' % es.replace('"', '\\"')
            c = src.count(alvo)
            if c:
                sobras.setdefault(es, []).append(f"{os.path.relpath(p, a.raiz)}:{c}")
    print()
    if sobras:
        print("ATENCAO - sobraram ocorrencias do literal antigo (revisar):")
        for es, locs in sobras.items():
            print(f"   {es!r}: {', '.join(locs)}")
    else:
        print("verificacao ok: nenhuma ocorrencia dos literais antigos restante")

if __name__ == "__main__":
    main()
