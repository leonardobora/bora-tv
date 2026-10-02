# IPTVnator na TCL 55P8K (Google TV) — veredito, APK e plano

Data: 29/09/2026 · alvo: TCL 55P8K Google TV (BR) e/ou TV box
Fonte: https://github.com/4gray/iptvnator (oficial) + PR #1699

---

## 1. VEREDITO

Dá, e o APK já existe: **compilado e assinado nesta máquina**.

O app oficial (Electron + Angular)
[a]  não gera APK e nunca vai gerar sem reescrita — Electron não roda em Android.
A porta nativa para Android TV existe como contribuição de terceiros, não mergeada:
PR #1699 em 4gray/iptvnator, diretório `android-tv/`, Kotlin + Compose for TV + Media3.

O trabalho real, portanto, não é *escrever* um app de IPTV para TV — é
**forkar 30 mil linhas de Kotlin que já existem, consertar a navegação por
controle remoto e conviver com o fato de ninguém manter isso.**

## 2. ARTEFATO GERADO E VERIFICADO

    /home/bora/Work/iptvnator-tv/dist/iptvnator-tv-0.1.0-unofficial.apk
      tamanho   3.815.902 bytes (3,7 MB)
      sha256    63e6b2597364f5edd826d59c1e3cc8c4e3209c139a04a605db26f45f0ef471d3
      pacote    com.iptvnator.googletv   versionName 0.1.0-tv
      minSdk    23 (Android 6+)          targetSdk 36 (Android 16)
      ABIs      arm64-v8a, armeabi-v7a, x86, x86_64  (APK universal — roda em TV ARMv7 32-bit)
      launcher  LEANBACK_LAUNCHER + LAUNCHER, banner 320x180, landscape fixo
      assinado  keystore própria (CN=IPTVnator TV (unofficial personal build))
                SHA-256 do certificado: d4503b4ae75798dce584db01f84c0ee37cad096f88a7b247c76993ebe079a26d

    Fonte: commit 71a2d988a9197915baa93f301120cf4f9becd2ba (fork Antaneyes/iptvnator, branch android-tv-port)
    Build: ./gradlew :app:assembleRelease — BUILD SUCCESSFUL em 6m36s
    Script reprodutível: /home/bora/Work/iptvnator-tv/build-apk.sh  (./build-apk.sh --sign)

    Toolchain (tudo rootless, sem pacman):
      JDK 21.0.12.1 Temurin      -> ~/.local/opt/jdk21 (API da Adoptium)
      Android SDK cmdline-tools  -> ~/Android/Sdk  (platform-tools, platforms;android-36, build-tools;36.0.0)
      Gradle 9.5.0 (wrapper do projeto) + AGP 8.13.2 + Kotlin 2.2.20

### Instalar na TV

    # 1. na TV: Settings > System > About > "Android TV OS build" x7  (libera Developer options)
    # 2. Developer options > USB debugging = ON
    # 3. no PC, mesma rede:
    adb connect <IP_DA_TV>:5555      # aceite o popup na TV
    adb install -r /home/bora/Work/iptvnator-tv/dist/iptvnator-tv-0.1.0-unofficial.apk
    # opcional: compilar AOT na hora em vez de esperar o dexopt
    adb shell cmd package compile -m speed -f com.iptvnator.googletv

    # conferir se o aparelho serve (roda na própria TV):
    adb shell getprop ro.build.version.release ; adb shell getprop ro.build.version.sdk
    adb shell getprop ro.product.cpu.abi ; adb shell getprop ro.product.cpu.abilist
    adb shell pm list features | grep leanback ; adb shell df -h /data

Sem PC: instalar o app **Downloader** (AFTVnews) pela Play Store da TV,
apontar para uma URL do APK (ou mover por pendrive/Drive) e liberar
"Unknown sources" para ele.

## 3. O QUE A PORTA É (números reais, medidos)

    63 arquivos Kotlin em main, 30.211 linhas
      7.104 linhas  TvApp.kt  (banner: 727 KB — telas, navegação e estado do app inteiro)
      5.983 linhas  playlist/ (parser M3U, store SQLite + migrações, backup)
      2.715 linhas  playback/ (Media3: HLS, DASH+ClearKey, TS, MP4)
      1.097 linhas  recording/ (gravação de live)
      1.059 linhas  xtream/    820 stalker/    947 download/    258 epg/
    Testes: 55 arquivos unitários (3.778 linhas) + 33 de instrumentação (9.907 linhas)

    Funciona (segundo o autor, e o código confirma a estrutura): M3U por URL/arquivo/texto,
    Xtream (catálogos grandes, import cancelável), Stalker/Ministra, EPG XMLTV com catch-up,
    filmes/séries com resume + TMDB, downloads resumíveis, gravação ao vivo,
    backup JSON **compatível com o desktop**.

    Defeito nº 1: **foco do D-pad**. Diagnóstico no código:
      FocusRequester/modificador   1.064 ocorrências  (foco ad-hoc espalhado)
      focusProperties                 93
      focusRestorer                    0   <- não existe restauração de foco
      focusGroup                       0   <- listas sem agrupamento de foco
    Ou seja: foco tratado caso a caso, sem restauração e sem agrupamento — exatamente
    o que produz "o foco pula/some/precisa apertar duas vezes" num controle remoto.

    Outros: UI só em espanhol com strings hard-coded; TvApp.kt a ser fatiado;
    release assinado com debug key; **usesCleartextTraffic=true** (aceita HTTP puro,
    prático para IPTV mas é uma porta aberta); allowBackup=true (risco apontado no
    review do PR: o backup restaura preferências cifradas sem as chaves do Keystore
    original e as credenciais do provedor morrem).

## 4. PLANO EM FASES

    FASE 0 — feita
      [x] toolchain rootless + build + assinatura + script reprodutível
      [x] APK universal verificado (ABIs, minSdk, leanback, sha256)

    FASE 1 — 1 tarde: rodar na TV
      [ ] developer options + adb connect na 55P8K, instalar, abrir pelo launcher
      [ ] importar uma fonte LEGAL (M3U público ou Xtream próprio) e medir:
          zapping entre canais, estabilidade de HLS, .ts legado, EPG de um dia,
          comportamento de memória com catálogo grande
      [ ] confirmar bitness do userland e versão do Android da TV
      Saída: veredito "usável hoje" ou lista de bloqueios.

    FASE 2 — o trabalho que importa: consertar o controle remoto
      [ ] camada de foco: restauração após recarregar lista, focusGroup nos rails,
          texto só com "OK para digitar" (matar o teclado virtual automático)
      [ ] TvApp.kt fatiado em telas/viewmodels (o arquivo de 7 mil linhas é o
          bloqueio para qualquer mudança maior)
      [ ] os 3 bugs P1 do review do PR: resume de filme no restore de backup,
          gravação órfã ao recriar a activity, backup/Keystore
      Esforço honesto: dias, não horas — e é onde o projeto vive ou morre.

    FASE 3 — qualidade de vida
      [ ] strings para res/values + values-pt/values-pt-rBR (PT-BR de verdade)
      [ ] nome/appId/ícone próprios, keystore própria (já temos), README de fork
      [ ] repo próprio com o diretório android-tv/ vendorizado

    FASE 4 — opcional, se quiser compartilhar
      [ ] GitHub Releases com APK assinado + oferta de código-fonte no mesmo tag
          (obrigação GPL-3 — ver DECISAO-licenca-distribuicao.md)
      [ ] Play Store: NÃO. Exige navegação 5-way completa (TV-DP), que é justamente
          o defeito nº 1, e o TRADEMARK.md proíbe o nome.

## 5. OS TRÊS CAMINHOS (e por que este)

    A) Porta NATIVA (esta) — Kotlin/Compose/Media3, PR #1699.
       Prós: player de TV de verdade, Media3 nativo, APK universal 3,7 MB, sem servidor.
       Contras: ninguém mantém, espanhol, foco quebrado, 30k linhas "vibe-coded".

    B) Wrapper Capacitor da PWA — fork guchumu/iptvnator (MIT, push 28/09/2026).
       Empacota o app Angular num WebView + plugin nativo ExoPlayer/LibVLC + pareamento por QR.
       Prós: paridade total com o desktop (inclusive os 16 idiomas, PT-BR já pronto).
       Contras: o APK dele aponta `server.url` para uma PWA hospedada em domínio de
       terceiro (acortador.vip) — sem PWA própria o app não abre; o CI nunca rodou
       (nenhum artifact gerado); e o próprio autor documenta os limites da abordagem
       no Google TV Streamer (ExoPlayer/LibVLC no mesmo processo do WebView aborta
       quando você mexe no controle; milhares de logos remotos saturam o WebView).
       Observação técnica: MSE **existe** no WebView do Android (MDN: WebView Android 4.4.3+),
       então hls.js não é o impedimento — o impedimento é decodificação/UX de TV.

    C) Não forkar nada — usar o que já existe:
       OwnTV (github.com/ahXN00/OwnTV, GPL-3.0, 468 estrelas, push 28/09/2026, APKs no
       Releases v5.0.4): Kotlin + Compose for TV + ExoPlayer/mpv, M3U + Xtream + Stalker +
       EPG + catch-up, feito para controle remoto. Também: TiviMate (pago), OTT Navigator,
       Televizo (com anúncios), Kodi + pvr.iptvsimple (GPL-2, sem login Xtream).

    Escolha: **A** para "quero IPTVnator na TV e gosto do problema";
    **C (OwnTV)** se o objetivo é "assistir meus canais hoje à noite".
    O diferencial real de A é a paridade com o IPTVnator desktop (o backup JSON é
    compatível) e o controle total sobre um build sem anúncio e sem telemetria.

## 6. RISCOS E O QUE NÃO FOI VERIFICADO

    [ ] Não rodei o app em hardware nenhum. Build ✓ ≠ funciona ✓. Fase 1 existe por isso.
    [ ] D-pad: só medi os padrões no código; não senti o comportamento na mão.
    [ ] Specs da 55P8K BR: Google TV, 144 Hz, 3 GB RAM, CA75+CA55 — de agregador de
        especificações; a ficha da Fastshop diz só "Android". Confirmar na própria TV.
    [ ] A porta usa `usesCleartextTraffic=true` e assina release com debug key por padrão:
        ótimo para sideload pessoal, ruim como postura de segurança.
    [ ] Upstream se move rápido (último push no dia desta análise): a porta não acompanha.
    [ ] Licença: `android-tv/` é GPL-3.0-or-later dentro de um repo MIT. Uso pessoal = zero
        obrigação; distribuir = código-fonte junto. Detalhes no DECISAO-licenca-distribuicao.md.

## 7. ARQUIVOS

    build-apk.sh                       build reprodutível (--sign usa a keystore própria)
    dist/iptvnator-tv-0.1.0-unofficial.apk   o APK instalável
    keystore/iptvnator-tv.jks + keystore-password.txt (chmod 600)   chave de update
    DECISAO-licenca-distribuicao.md    licença, marca, canal de distribuição, alternativas
    android-tv/                        o projeto-fonte (commit 71a2d98)
