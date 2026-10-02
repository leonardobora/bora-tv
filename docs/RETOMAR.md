# RETOMAR AQUI — IPTVnator TV em português

Parado em 29/09/2026 à noite, a pedido (compromisso do Bora). **Nada perdido**: tudo
commitado no git local, APK assinado no disco, toolchain instalada.

Repo de trabalho: `/home/bora/Work/iptvnator-tv` (branch local `ptbr`, base = commit
71a2d98 da porta do PR #1699). **Nada foi enviado ao GitHub** — nenhum commit remoto.

---

## 1. O ESTADO REAL

APK atual (compilado, assinado com a keystore própria; instala por cima de qualquer
versão anterior sem perder dados):

    /home/bora/Work/iptvnator-tv/dist/iptvnator-tv-0.2.0-tv-ptbr-unofficial.apk
      sha256   234372ccceabf738106e0f40204146ce15a2d552ca81197a030987281054b674
      versão   0.2.0-tv-ptbr (versionCode 2)  ·  minSdk 23 / targetSdk 36
      assinado CN=IPTVnator TV (unofficial personal build)
      cert SHA-256 d4503b4ae75798dce584db01f84c0ee37cad096f88a7b247c76993ebe079a26d

    Rebuild:  cd /home/bora/Work/iptvnator-tv && ./build-apk.sh --sign   (~2 min)

Na TV TCL (192.168.18.32:5555): porta instalada e rodando, catálogo Xtream real do Bora
importado (3314 canais), e a fonte sobreviveu a todas as reinstalações.

## 2. TRADUÇÃO — FEITO

    444 strings de UI em português, 439+ call sites localizados em 17 arquivos
    base PT-BR em res/values/  +  espanhol preservado em res/values-es/
    menu lateral, rail de Configurações, diálogos, erros e mensagens de estado em PT

Por que não foi find-and-replace (o que dói nesse código):

  1. `tools-i18n/extrair_strings.py` — scanner de literais Kotlin que entende `${expr}`
     e `$var`, e separa texto de UI de SQL/nome de coluna por heurística.
  2. `tools-i18n/renomear.py` — vocabulário que é **chave de dispatch e rótulo ao mesmo
     tempo** (`listOf("Geral", ...)` + `when (selected) { "Geral" -> ... }`, chips de
     filtro). Traduzir só a exibição quebraria o filtro em silêncio; então o literal é
     trocado em TODAS as ocorrências, com verificação por grep (zero sobras do antigo).
  3. `tools-i18n/traduzir.py` — classifica cada site (exibição vs. chave de lógica, pela
     vizinhança imediata do literal, não a linha inteira), gera os dois strings.xml e
     reescreve os call sites para `str(R.string.x, args)`.
  4. `tools-i18n/consertar_vars.py` — conserta sites que perderam `$var` na primeira
     passada (o scanner antigo só entendia `${...}`).

Strings próprias do fork (créditos) entram pelo dicionário `MANUAIS` do traduzir.py.

## 3. PENDENTE

    351 strings de UI ainda em espanhol (461 sites). As mais visíveis:
      "Buscar en todas las playlists..."   (placeholder da busca no topo)
      "Configura el aspecto y el comportamiento inicial de la aplicación."
      "Oscuro"  -> deve virar "Escuro" (opção de tema)
      nomes de passo do progresso de import, mensagens de download e gravação

    Material pronto para terminar: i18n/faltam-{1,2,3}.json têm ~287 strings divididas
    em 3 lotes (mesmo formato que já funcionou duas vezes nesta sessão). 3 entradas com
    template `$var` ficaram de fora de propósito.

    Para terminar:
      1. traduzir os 3 lotes -> i18n/traducao-N.json
      2. juntar tudo em i18n/traducao.json
      3. cd android-tv/tools-i18n && python3 traduzir.py --raiz ../app/src/main \
           --i18n /home/bora/Work/iptvnator-tv/i18n --aplicar
      4. cd /home/bora/Work/iptvnator-tv && ./build-apk.sh --sign
      5. adb install -r dist/<apk gerado>

    NOTAS DOS TRADUTORES (revisar terminologia numa próxima passada):
      - "EPG" foi traduzido como "guia" em várias strings; se preferir manter a sigla
        EPG (mais curta na tela), é só ajustar as entradas com "guia" no traducao.json.
      - "Dashboard" ficou "Painel" no rail de Configurações (passo de renomeação), mas
        algumas strings ainda dizem "Mostrar Dashboard" -> padronizar num dos dois.
      - "live" (minúsculo) foi copiado como valor de máquina; o rótulo visível é
        "AO VIVO". Confirmar se algum lugar mostra "live" cru.
      - Tokens copiados de propósito e que NÃO devem ser traduzidos (são comparados por
        igualdade no código): "medium" (poster_size), "favorites" (escopo de coleção),
        "vod"/"all"/"small"/"identity", mime types e fragmentos de SQL.

## 4. ÍCONE — DECISÃO ABERTA

Já aplicado e rodando: marca própria em vetor (`res/drawable/ic_launcher.xml`), fundo
vermelho #E01A2B com contorno branco de tela + antena + play; banner 320x180 em degradê
vermelho (`tv_banner.xml`). O launcher do Google TV já mostra o ícone vermelho.

O ícone do Flaticon que o Bora mandou (`jogar_7324690`) tem **dois problemas**:

  1. Não é glifo chapado — é disco com gradiente amarelo/laranja e triângulo branco.
     Sobre vermelho briga, e pintar tudo de branco apaga o triângulo.
  2. **A Flaticon bloqueou o acesso** (403 no curl e também no navegador real), então
     não deu para pegar o nome do autor — que é a atribuição obrigatória da licença
     gratuita deles — nem confirmar se o asset é Free ou Premium. Num APK que pode ser
     publicado (e que, distribuído, tem de ser GPL), é risco que não se assume sem saber.

Prévias para decidir olhando (3 variantes lado a lado):
    /home/bora/.hermes/cache/scratch/icone/preview-icones.png
      A) marca própria (a que está no ar)   B) Flaticon como veio   C) Flaticon negativo

Se quiser mesmo o do Flaticon: baixar logado no site, mandar o arquivo + nome do autor,
e eu embuto + coloco a atribuição no "Sobre" e num CREDITS.

## 5. O QUE MUDOU NESTA SESSÃO (além da tradução)

    - Bloco "Sobre" em Configurações com os créditos:
      "Adaptado e mantido por Leonardo Bora · github.com/leonardobora", base MIT/4gray
      + GPL-3.0-or-later do android-tv/, e o aviso de build não oficial.
    - A linha "Idioma" das Configurações mentia ("Español"); agora mostra o idioma real
      do sistema (o app segue o idioma do Android, base PT-BR).
    - Bug que apareceria na tela, corrigido: o gerador escrevia `{1}` nos recursos em vez
      de `%1$s`, então `getString(id, args)` ignorava o argumento e a TV mostraria
      "{1} canais". Agora 83 recursos usam marcador de formato correto.
    - `build-apk.sh` nomeia o APK a partir da versão, e o versionCode subiu para 2.

## 6. COMO VOLTAR

    # TV (developer options + USB debugging já estão ligados)
    adb connect 192.168.18.32:5555
    adb install -r /home/bora/Work/iptvnator-tv/dist/iptvnator-tv-0.2.0-tv-ptbr-unofficial.apk
    adb shell cmd package compile -m speed -f com.iptvnator.googletv

    # recompilar (o script põe JAVA_HOME e ANDROID_HOME)
    cd /home/bora/Work/iptvnator-tv && ./build-apk.sh --sign

    # servir arquivos para a TV sem sudo (porta 53317 já liberada no ufw)
    cd /home/bora/Work/iptvnator-tv/share && python3 -m http.server 53317 --bind 0.0.0.0

    # porta 8000 exigiria: sudo ufw allow from 192.168.18.0/24 to any port 8000 proto tcp

## 7. FASES DO PROJETO

    Fase 1 (hardware)   FEITA — instalado, rodando, 3314 canais reais, sem crash
    Fase 2 (D-pad)      NÃO COMEÇADA — segue o defeito nº 1 do port
                        (1.064 FocusRequester, 0 focusRestorer, 0 focusGroup)
    Fase 3 (PT-BR)      EM ANDAMENTO — 444 de ~800 strings feitas
    Fase 4 (publicar)   NÃO COMEÇADA — exige nome/appId/ícone próprios; keystore ok
    Decisão em aberto   forkar de vez ou ir de OwnTV (GPL-3, pronto, mantido)

## 8. CAPTURA DE USO — FERRAMENTAS PRONTAS E ACHADOS

Ferramentas em `tools-uso/` (nenhuma altera o app):

    capturar-sessao.sh   grava uma sessão inteira pelo adb: logcat completo, getevent
                         (cada tecla do controle), screenrecord + quadros a 1 fps,
                         screenshot a cada 30 s, gfxinfo/meminfo a cada 5 s, INFO.txt
                         Uso: ./capturar-sessao.sh 900 sessao-do-amigo
    analisar-sessao.py   lê a pasta e gera RELATORIO.md: jank no tempo, memória,
                         fluxo de telas com permanência, teclas, crash/ANR, erros
    sessoes/             saída (fora do git)

**ACHADO 1 — crash real, reproduzido em 45 s de captura:**
    java.lang.IllegalStateException: Session ID must be unique. ID=
    Origem: android-tv/.../playback/TvPlaybackController.kt:114
            private val mediaSession = MediaSession.Builder(context, player).build()
    Sem .setId(), o Media3 usa ID vazio e exige unicidade por processo; um segundo
    controller (recriação de activity/recomposição) derruba o app. O Android reiniciou.
    Correção: id único explícito + garantir controller único (singleton) e release().

**ACHADO 2 — travamento medido, não sentido:**
    43% dos quadros são janky, e PIORA durante o uso (40,5% -> 44,9% numa sessão de 45 s),
    com PSS subindo de 96 MB para 106 MB numa TV de 2,4 GB. Isso é o "engasga" do port,
    agora com número.

**O QUE A CAPTURA EXTERNA NÃO RESPONDE** (precisa instrumentar dentro do app):
    - D-pad que não muda o foco (o foco anda dentro da MESMA janela: invisível de fora)
    - qual elemento estava focado em cada aperto
    - tempo até o primeiro canal e tempo de zapping

Desenho da instrumentação (fase 2 do trabalho de uso), se for seguir:
    - TvTelemetry: JSONL em filesDir, com rotação; eventos com timestamp monotônico
    - pontos de gancho: TvDpad.kt (TODO aperto de controle passa por lá -> é o lugar
      único para medir "aperto que não mudou o foco"), troca de tela (dwell ms),
      TvPlaybackController (zap_start/zap_ready/erro)
    - privacidade: sem credenciais (o AGENTS.md do repo proíbe), sem nome de canal por
      padrão (hash), sem identificador de usuário, opt-in explícito e exportar sob demanda
    - NÃO usar Firebase/analytics remoto sem tela de consentimento (LGPD + é a TV de outra
      pessoa; o app guarda credenciais do provedor)
