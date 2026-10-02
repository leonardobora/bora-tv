# Bora TV

Player de IPTV para Android TV, Google TV e celular (Android 6+), em português.

É um build **não oficial** e em português do app [IPTVnator](https://github.com/4gray/iptvnator)
para Android TV. O aplicativo **não fornece canais, playlists nem assinaturas** — você
aponta ele para a sua própria fonte (M3U, Xtream Codes ou portal Stalker), igual ao
IPTVnator de desktop, ao TiviMate ou ao VLC.

| | |
|---|---|
| Pacote | `io.github.leonardobora.boratv` |
| Versão | 0.3.0 |
| Requisitos | Android 6.0+ (API 23) · ARMv7, ARM64, x86, x86_64 |
| Testado em | TCL 55P8K (Google TV, Android 14) · Galaxy S21 (Android 13) |
| Licença | GPL-3.0-or-later (ver [LICENSE](LICENSE) e [NOTICE](NOTICE)) |

## O que funciona

- Fontes: M3U/M3U8 por URL, arquivo ou texto colado; **Xtream Codes** (canais, filmes,
  séries, catálogos grandes) e **Stalker/Ministra**; User-Agent/Referer/Origin por fonte
- Ao vivo: grupos, favoritos, recentes, busca, número de canal, zapping por CH+/CH−
- Filmes e séries: página de detalhe, temporadas, episódios, retomada, TMDB opcional
- Player: HLS, DASH (inclui ClearKey), MPEG-TS e MP4, seleção de faixa/legenda,
  legendas externas SRT/VTT/SSA, reconexão automática, avanço de episódio
- EPG XMLTV com linha do tempo, busca de programa e catch-up/start-over
- Downloads e gravação de canal ao vivo
- Interface em português (base) com espanhol preservado em `res/values-es/`

## O que ainda não está bom

- **Foco do controle remoto**: é a maior deficiência herdada. O foco às vezes cai no
  elemento errado, se perde ao recarregar uma lista ou exige um aperto extra. Com o
  teclado virtual aberto, o direcional não sai do campo sem fechar o teclado.
- **Tradução incompleta**: cerca de 350 textos de tela ainda estão em espanhol
  (mensagens de erro, passos de importação, algumas opções de Configurações).
- Sem layout dedicado para celular: a interface é a de TV, forçada em paisagem.
- Sem suporte a LG webOS — é Android, não webOS. Em TV LG use um Chromecast/TV box.

## Instalar

**Pelo celular ou TV, direto:** baixe o APK na aba
[Releases](https://github.com/leonardobora/bora-tv/releases) e abra o arquivo no
aparelho. Em Android TV, o app precisa aparecer na fileira de apps do launcher.

**Por adb, do computador:**

```bash
adb connect <IP_DO_APARELHO>:5555     # TV: ligue Developer options + USB debugging
adb install -r bora-tv-0.3.0.apk
adb shell cmd package compile -m speed -f io.github.leonardobora.boratv
```

**Por F-Droid:** adicione este repositório em F-Droid → Configurações → Repositórios:

```
https://leonardobora.github.io/bora-tv/repo
```

## Compilar

Precisa de JDK 17+ e do Android SDK (platform 36 e build-tools 36.0.0). Não precisa de
Android Studio:

```bash
git clone https://github.com/leonardobora/bora-tv.git
cd bora-tv/android-tv
export JAVA_HOME=/caminho/para/jdk21
export ANDROID_HOME=/caminho/para/Android/Sdk
./gradlew :app:assembleRelease
# APK em app/build/outputs/apk/release/app-release.apk
```

O APK gerado sai assinado com a debug key do Android, o que serve para testar. Para
distribuir, assine com a sua própria chave (`apksigner`). O workflow em
`.github/workflows/build-apk.yml` faz isso automaticamente em tags `v*`, usando os
secrets `KEYSTORE_BASE64`, `KEYSTORE_PASSWORD`, `KEY_ALIAS` e `KEY_PASSWORD`.

## Tradução

A base é português em `android-tv/app/src/main/res/values/`, com o espanhol original
preservado em `res/values-es/`. As ferramentas que fizeram isso estão em
`android-tv/tools-i18n/` e os mapas de tradução em `i18n/`:

```bash
cd android-tv/tools-i18n
python3 extrair_strings.py ../app/src/main ../../i18n   # levantamento
python3 renomear.py --raiz ../app/src/main --mapa ../../i18n/renomear.json --aplicar
python3 traduzir.py --raiz ../app/src/main --i18n ../../i18n --aplicar
```

O `renomear.py` existe porque parte do vocabulário é, ao mesmo tempo, **chave de
dispatch e rótulo na tela** (`listOf("Geral", ...)` + `when (selected) { "Geral" -> ... }`):
traduzir só a exibição quebraria o filtro em silêncio.

## Uso e privacidade

O app **não tem telemetria**, não manda nada para servidor nenhum e não inclui
identificador de usuário. As credenciais da sua fonte ficam cifradas no Keystore do
aparelho, e o backup do Android está desligado de propósito (`allowBackup="false"`)
porque o Keystore não é restaurado junto — restaurar as preferências sem a chave
quebraria as credenciais.

Para estudar usabilidade existe `tools-uso/`, que grava uma sessão de uso **de fora do
app**, pelo adb (logs, teclas do controle, vídeo, jank, memória). Nada disso sai do
computador que roda a captura.

## Créditos e licenças

- **IPTVnator** — aplicação de desktop em Angular/Electron, de [4gray](https://github.com/4gray),
  licença MIT. Conceitos, formatos de fonte e comportamento serviram de referência.
- **Porta Android TV** (`android-tv/`) — Kotlin + Compose for TV + Media3, contribuição
  de [Antaneyes](https://github.com/Antaneyes) enviada como PR #1699 ao IPTVnator.
  Licença **GPL-3.0-or-later**.
- **Tradução PT-BR, correções e ferramentas** — Leonardo Bora.

O texto da licença MIT do IPTVnator está preservado em [NOTICE](NOTICE). O código em
`android-tv/` é GPL-3.0-or-later: se você distribuir um build, tem que oferecer o código
correspondente sob a mesma licença.

**Marca:** "IPTVnator" e o logo são marcas do autor original. Este projeto não é
afiliado, endossado nem patrocinado por ele; o nome do app aqui é outro justamente por
isso. Nada neste repositório vende, indica ou distribui assinatura de IPTV — é um
reprodutor, e o conteúdo é responsabilidade de quem aponta ele para uma fonte.
