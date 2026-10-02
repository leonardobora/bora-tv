#!/usr/bin/env bash
# capturar-sessao.sh — grava uma sessao de uso da TV para analise de usabilidade.
#
# NAO altera o aplicativo. Captura tudo pelo adb, do lado de fora:
#   logs/      logcat completo (main+system+crash) com timestamp de epoca
#   eventos/   getevent: cada tecla do controle, com o dispositivo de origem
#   frames/    screenshot a cada N segundos
#   video/     screenrecord da sessao inteira + quadros extraidos a 1 fps
#   amostras/  gfxinfo (jank) e meminfo a cada 5 s
#   INFO.txt   versao do app, modelo da TV, SDK, ABI, janela em foco
#
# Uso:
#   ./capturar-sessao.sh                 # 10 minutos, nome automatico
#   ./capturar-sessao.sh 900 teste-amigo # 15 minutos, nome escolhido
#   Ctrl-C encerra antes e ainda gera o resumo.
#
# Depois: ./analisar-sessao.sh <pasta da sessao>   (resumo + anomalias de foco)

set -uo pipefail

DUR="${1:-600}"
NOME="${2:-sessao-$(date +%Y%m%d-%H%M%S)}"
TV_IP="${TV_IP:-192.168.18.32}"
DEV="$TV_IP:5555"
RAIZ="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUT="$RAIZ/sessoes/$NOME"
PKG="com.iptvnator.googletv"

export PATH="$HOME/Android/Sdk/platform-tools:$PATH"
mkdir -p "$OUT"/{logs,eventos,frames,video,amostras}

fim() {
  echo
  echo "== encerrando captura =="
  adb -s "$DEV" shell "pkill -f 'logcat' ; pkill -f screenrecord" >/dev/null 2>&1
  sleep 2
  adb -s "$DEV" pull /sdcard/sessao.mp4 "$OUT/video/sessao.mp4" >/dev/null 2>&1
  adb -s "$DEV" shell rm -f /sdcard/sessao.mp4 >/dev/null 2>&1
  if [ -s "$OUT/video/sessao.mp4" ] && command -v ffmpeg >/dev/null; then
    echo "  extraindo quadros a 1 fps do video..."
    ffmpeg -loglevel error -i "$OUT/video/sessao.mp4" -vf fps=1 "$OUT/video/q-%04d.png" 2>/dev/null
    echo "  quadros: $(ls "$OUT/video"/q-*.png 2>/dev/null | wc -l)"
  fi
  ANALISADOR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/analisar-sessao.py"
  if [ -f "$ANALISADOR" ]; then
    python3 "$ANALISADOR" "$OUT" | tail -40
  fi
  echo
  echo "sessao salva em: $OUT"
  exit 0
}
trap fim INT TERM

echo "== conectando em $DEV"
adb connect "$DEV" >/dev/null 2>&1
if ! adb -s "$DEV" shell true >/dev/null 2>&1; then
  echo "ERRO: TV inalcancavel em $DEV (developer options ligado? mesma rede?)" >&2
  exit 1
fi

{
  echo "sessao:      $NOME"
  echo "inicio:      $(date -Iseconds)"
  echo "duracao:     ${DUR}s"
  echo "--- TV"
  for p in ro.product.manufacturer ro.product.model ro.build.version.release \
           ro.build.version.sdk ro.product.cpu.abilist ro.build.characteristics; do
    echo "  $p = $(adb -s "$DEV" shell getprop $p 2>/dev/null | tr -d '\r')"
  done
  echo "--- app"
  adb -s "$DEV" shell dumpsys package $PKG 2>/dev/null | grep -E "versionName|versionCode" | head -2 | tr -d '\r' | sed 's/^/  /'
  echo "--- janela em foco no inicio"
  adb -s "$DEV" shell dumpsys window 2>/dev/null | grep -m1 mCurrentFocus | tr -d '\r' | sed 's/^/  /'
} > "$OUT/INFO.txt"
cat "$OUT/INFO.txt"

# --- capturas paralelas ------------------------------------------------------
adb -s "$DEV" logcat -c >/dev/null 2>&1
adb -s "$DEV" logcat -v epoch -b main,system,crash > "$OUT/logs/tudo.log" 2>&1 &
LOGPID=$!
# getevent: cada tecla do controle (o shell tem acesso a /dev/input na maioria das TVs)
timeout "$DUR" adb -s "$DEV" shell getevent -lt > "$OUT/eventos/teclas.txt" 2>&1 &
# video da sessao (limite duro do proprio screenrecord)
adb -s "$DEV" shell screenrecord --bit-rate 4M --time-limit "$DUR" /sdcard/sessao.mp4 >/dev/null 2>&1 &

echo "== gravando por ${DUR}s  (Ctrl-C encerra antes) =="
INI=$(date +%s)
while :; do
  AGORA=$(date +%s); DEC=$(( AGORA - INI ))
  [ "$DEC" -ge "$DUR" ] && break
  # amostra de fluidez e memoria
  GFX=$(adb -s "$DEV" shell dumpsys gfxinfo $PKG 2>/dev/null | tr -d '\r')
  TOT=$(echo "$GFX" | sed -n 's/.*Total frames rendered: \([0-9]*\).*/\1/p' | head -1)
  JAN=$(echo "$GFX" | sed -n 's/.*Janky frames: \([0-9]*\) (\([0-9.]*\)%).*/\1 \2/p' | head -1)
  MEM=$(adb -s "$DEV" shell dumpsys meminfo $PKG 2>/dev/null | awk '/TOTAL/{print $2; exit}' | tr -d '\r')
  FOC=$(adb -s "$DEV" shell dumpsys window 2>/dev/null | grep -m1 mCurrentFocus | tr -d '\r' | sed 's/.*u0 //; s/}.*//')
  echo -e "$DEC\t${TOT:-?}\t${JAN:-?}\t${MEM:-?}\t$FOC" >> "$OUT/amostras/fluidez.tsv"
  # quadro a cada 30 s
  if [ $(( DEC % 30 )) -lt 5 ]; then
    adb -s "$DEV" shell screencap -p /sdcard/f.png >/dev/null 2>&1
    adb -s "$DEV" pull /sdcard/f.png "$OUT/frames/f-$(printf %04d $DEC).png" >/dev/null 2>&1
    adb -s "$DEV" shell rm -f /sdcard/f.png >/dev/null 2>&1
  fi
  sleep 5
done

kill "$LOGPID" 2>/dev/null
fim
