#!/usr/bin/env bash
# Regenera o repositorio F-Droid auto-hospedado e publica no GitHub Pages.
#
# Uso:  ./atualizar-repo.sh /caminho/para/o/apk-assinado.apk [versionCode]
#
# O APK tem que estar assinado com a chave de release do app (a mesma de sempre),
# senao o F-Droid recusa atualizar por cima da versao instalada.
#
# Requisitos:
#   - fdroidserver instalado como ferramenta uv:
#       uv tool install --python 3.12 --with androguard fdroidserver
#   - config.yml e keystore.p12 nesta pasta (nao versionados; a chave do repositorio
#     fica so na sua maquina). Na primeira vez: veja "Primeira vez" no fim.
#
# ARMADILHAS ja resolvidas aqui (cada uma custou tempo para achar):
#   1. PYTHONPATH do shell aponta para outro venv e o fdroid importa o PIL errado
#      -> sempre rodar com `env -u PYTHONPATH -u PYTHONHOME`.
#   2. Com androguard 4.x o `format_value` devolve bytes, e o
#      `value.startswith('0x')` do fdroidserver estoura TypeError: o versionCode
#      sai None e o indice passa a ser chaveado por hash. O patch abaixo conserta.
#   3. O fdroidserver so cai no aapt em caso de zip corrompido; o `aapt` no
#      config.yml fica como rede de seguranca.

set -euo pipefail

APK="${1:?uso: ./atualizar-repo.sh <apk-assinado> [versionCode]}"
cd "$(dirname "$0")"

FDROID="$HOME/.local/share/uv/tools/fdroidserver/bin/fdroid"
PY="$HOME/.local/share/uv/tools/fdroidserver/bin/python"
COMMON="$HOME/.local/share/uv/tools/fdroidserver/lib/python3.12/site-packages/fdroidserver/common.py"

[ -x "$FDROID" ] || { echo "fdroidserver nao encontrado em $FDROID"; exit 1; }
[ -f config.yml ] || { echo "config.yml ausente nesta pasta"; exit 1; }

# --- armadilha 2: patch do bytes no androguard 4.x (idempotente)
if [ -f "$COMMON" ] && ! grep -q "androguard 4.x devolve bytes" "$COMMON"; then
  echo "aplicando patch do androguard 4.x em $COMMON"
  "$PY" - "$COMMON" <<'PY'
import sys
p = sys.argv[1]
src = open(p, encoding="utf-8").read()
old = """                        value = format_value(_type, _data, lambda _: axml.getAttributeValue(i))
                        if appid is None and name == 'package':"""
new = """                        value = format_value(_type, _data, lambda _: axml.getAttributeValue(i))
                        if isinstance(value, bytes):  # androguard 4.x devolve bytes
                            value = value.decode('utf-8', 'replace')
                        if appid is None and name == 'package':"""
if old not in src:
    print("  padrao nao encontrado (versao diferente do fdroidserver?)")
    sys.exit(0)
open(p, "w", encoding="utf-8").write(src.replace(old, new, 1))
print("  ok")
PY
fi

# --- le o id do APK e monta o nome de arquivo que o fdroid espera
ID=$(env -u PYTHONPATH -u PYTHONHOME "$PY" - "$APK" <<'PY'
import sys
from fdroidserver import common
print("\t".join(str(x) for x in common.get_apk_id(sys.argv[1])))
PY
)
APPID=$(echo "$ID" | cut -f1)
VCODE=$(echo "$ID" | cut -f2)
VNAME=$(echo "$ID" | cut -f3)
echo "APK: $APPID  versionCode=$VCODE  versionName=$VNAME"
[ "$VCODE" != "None" ] || { echo "versionCode nao lido: veja a armadilha 2"; exit 1; }

mkdir -p repo
cp -f "$APK" "repo/${APPID}_${VCODE}.apk"

# --- regenera o indice (sem cache: o cache do fdroidserver segura entradas velhas)
rm -rf tmp
env -u PYTHONPATH -u PYTHONHOME "$FDROID" update

echo "indice: $(ls repo/index-v1.jar repo/index-v2.json 2>/dev/null | tr '\n' ' ')"

# --- confere o que o cliente F-Droid vai ler
env -u PYTHONPATH -u PYTHONHOME "$PY" - <<PY
import json, zipfile
d = json.loads(zipfile.ZipFile("repo/index-v1.jar").read("index-v1.json"))
for a in d["apps"]:
    for v in d["packages"][a["packageName"]]:
        print(f"  {a['packageName']}  {a.get('name')}  versionCode={v['versionCode']}  {v['apkName']}")
PY

# --- publica no GitHub Pages (branch gh-pages, pasta repo/)
PAGES="$(mktemp -d)"
mkdir -p "$PAGES/repo"
cp -a repo/. "$PAGES/repo/"
cp -f pagina.html "$PAGES/index.html" 2>/dev/null || true
cd "$PAGES"
git init -q -b gh-pages
git add -A
git -c user.email=leonardobora@users.noreply.github.com -c user.name="Leonardo Bora" \
    commit -q -m "repo F-Droid: ${APPID} ${VNAME} (${VCODE})"
git remote add origin https://github.com/leonardobora/bora-tv.git
git push -f origin gh-pages
echo "publicado em https://leonardobora.github.io/bora-tv/repo"

# Primeira vez (para gerar config.yml e a chave do repositorio):
#
#   cd fdroid
#   PW=$(head -c 24 /dev/urandom | base64 | tr -d '/+=' | head -c 20)
#   keytool -genkeypair -keystore keystore.p12 -storetype PKCS12 -alias fdroid \
#     -keyalg RSA -keysize 4096 -validity 10000 -storepass "$PW" -keypass "$PW" \
#     -dname "CN=Leonardo Bora, OU=Bora TV, O=Leonardo Bora, L=Sao Paulo, ST=SP, C=BR"
#   cat > config.yml <<EOF
#   local_copy_dir: repo
#   keystore: keystore.p12
#   keystorepass: $PW
#   keypass: $PW
#   repo_keyalias: fdroid
#   keydname: CN=Leonardo Bora, OU=Bora TV, O=Leonardo Bora, L=Sao Paulo, ST=SP, C=BR
#   repo_url: https://leonardobora.github.io/bora-tv/repo
#   repo_name: Bora TV
#   repo_description: Build PT-BR do player IPTV para Android TV, Google TV e celular
#   repo_icon: icon-fonte.png
#   aapt: $HOME/Android/Sdk/build-tools/36.0.0/aapt2
#   archive_older: 2
#   EOF
#   chmod 600 config.yml keystore.p12
#
# Guarde a keystore.p12 e a senha: trocar essa chave obriga todo mundo a
# remover e adicionar o repositorio de novo no F-Droid.
