#!/usr/bin/env python3
"""analisar-sessao.py — le uma sessao capturada e cospe um relatorio de usabilidade.

Uso: python3 analisar-sessao.py ../sessoes/<nome>

O que ele responde, e o que NAO responde:

  RESPONDE (dado de fora do app, sem instrumentacao):
    - travamento real: evolucao dos quadros janky ao longo da sessao
    - pressao de memoria numa TV pequena
    - crash / ANR / excecao
    - fluxo de telas: sequencia de janelas em foco com tempo de permanencia
    - quantas teclas o controle mandou e quais
    - erros de reproducao que o proprio app registra

  NAO RESPONDE (precisa de instrumentacao dentro do app):
    - "apertei e nao aconteceu nada" (o foco se move dentro da MESMA janela,
      entao de fora e invisivel)
    - qual elemento estava focado quando o usuario apertou
    - tempo ate o primeiro canal, tempo de zapping
"""
import os, re, sys, collections, statistics

def ler(p):
    try:
        return open(p, encoding="utf-8", errors="ignore").read().splitlines()
    except OSError:
        return []

def analisar(d):
    out = []
    w = out.append
    w(f"# Relatorio de usabilidade — {os.path.basename(d.rstrip('/'))}")
    info = ler(os.path.join(d, "INFO.txt"))
    for l in info[:8]:
        w("  " + l)
    w("")

    # ---- fluidez ----------------------------------------------------------
    amostras = ler(os.path.join(d, "amostras/fluidez.tsv"))
    jan_ini = jan_fim = None
    mems = []
    for l in amostras:
        c = l.split("\t")
        if len(c) < 4:
            continue
        j = c[2].split(" ")
        if len(j) == 2:
            try:
                pct = float(j[1])
                if jan_ini is None:
                    jan_ini = pct
                jan_fim = pct
            except ValueError:
                pass
        try:
            mems.append(int(c[3]))
        except ValueError:
            pass
    w("## Fluidez (quadros janky acumulados)")
    if jan_ini is not None and jan_fim is not None:
        ini, fimm = float(jan_ini), float(jan_fim)
        w(f"  inicio: {ini:.1f}%   fim: {fimm:.1f}%   amostras: {len(amostras)}")
        if fimm > ini + 3:
            w("  -> PIOROU durante a sessao: o app acumulou travamento (memoria? listas grandes?)")
        elif fimm < ini - 3:
            w("  -> melhorou: custo de abertura (import/catalogo) diluido no uso")
    else:
        w("  sem amostras")
    if mems:
        w(f"  memoria PSS: min {min(mems)} kB · max {max(mems)} kB · fim {mems[-1]} kB")
        if max(mems) > 200_000:
            w("  -> ATENCAO: passou de 200 MB numa TV de 2,4 GB; risco de recarga de app")
    w("")

    # ---- fluxo de telas ---------------------------------------------------
    focos = [(c[0], c[4]) for c in (l.split("\t") for l in amostras) if len(c) >= 5 and c[4]]
    w("## Fluxo de telas (janela em foco, a cada 5 s)")
    if focos:
        seq = []
        for t, f in focos:
            if not seq or seq[-1][1] != f:
                seq.append([t, f, 1])
            else:
                seq[-1][2] += 1
        for t, f, n in seq:
            w(f"  t={t:>4}s  {f}  (~{n*5}s)")
        w(f"  trocas de tela: {len(seq)}")
    else:
        w("  sem dados")
    w("")

    # ---- teclas -----------------------------------------------------------
    ev = ler(os.path.join(d, "eventos/teclas.txt"))
    teclas = collections.Counter()
    for l in ev:
        m = re.search(r"KEY_([A-Z0-9_]+)\s+(DOWN|UP)", l)
        if m and m.group(2) == "DOWN":
            teclas[m.group(1)] += 1
    w("## Controle remoto (teclas pressionadas)")
    if teclas:
        total = sum(teclas.values())
        dpad = sum(v for k, v in teclas.items() if k.startswith("DPAD"))
        w(f"  total: {total}   de navegacao (DPAD): {dpad} ({100*dpad/max(total,1):.0f}%)")
        for k, v in teclas.most_common(10):
            w(f"    {v:4}x {k}")
        if dpad > 300:
            w("  -> muitas teclas de navegacao: cheiro de foco que nao anda (medir dentro do app)")
    else:
        w("  nenhuma tecla capturada (getevent sem permissao nesta TV?)")
    w("")

    # ---- crash / erro -----------------------------------------------------
    log = ler(os.path.join(d, "logs/tudo.log"))
    fat = [l for l in log if re.search(r"FATAL|AndroidRuntime|ANR in", l)]
    erros = [l for l in log if "iptvnator" in l.lower() and re.search(r"error|falhou|failed|exception", l, re.I)]
    w("## Estabilidade")
    w(f"  linhas de log: {len(log)}   crashes/ANR: {len(fat)}   erros do app: {len(erros)}")
    for l in fat[:5]:
        w("    " + l[:150])
    for l in erros[:8]:
        w("    " + l[:150])
    w("")

    w("## O que ainda falta medir (exige instrumentacao no app)")
    w("  - apertos de D-pad que nao mudam o foco  (foco anda dentro da mesma janela)")
    w("  - tempo ate o primeiro canal e tempo de troca de canal")
    w("  - elemento focado no momento de cada aperto")
    rel = os.path.join(d, "RELATORIO.md")
    open(rel, "w", encoding="utf-8").write("\n".join(out) + "\n")
    print("\n".join(out))
    print(f"\n-> salvo em {rel}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__); sys.exit(1)
    analisar(sys.argv[1])
