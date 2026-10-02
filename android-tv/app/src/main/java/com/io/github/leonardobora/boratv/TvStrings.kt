package io.github.leonardobora.boratv

import android.content.Context
import androidx.annotation.StringRes

/**
 * Acesso uniforme as strings localizadas do app.
 *
 * Por que existe: o port original tem ~750 textos de interface hard-coded em
 * espanhol, espalhados por 28 arquivos - parte em composables, parte em classes
 * que nao tem Context nenhum (repositorio, gerenciador de gravacao, clientes
 * Xtream/Stalker). `stringResource()` resolve so o primeiro caso, e injetar
 * Context em ~300 sitios de codigo nao-UI seria invasivo.
 *
 * Um Context de aplicacao guardado no onCreate() do TvApplication permite uma
 * unica forma de chamada em qualquer lugar: `str(R.string.nome_da_chave)`.
 *
 * Limite conhecido: nao recompoe se o idioma do sistema mudar com o app ja
 * aberto - o idioma e resolvido na abertura do processo. Migrar a camada de UI
 * para `stringResource` e um passo posterior, se isso incomodar.
 */
object TvStrings {
    private var app: Context? = null

    fun init(context: Context) {
        app = context.applicationContext
    }

    fun s(@StringRes id: Int, vararg args: Any): String {
        val ctx = app ?: throw IllegalStateException(
            "TvStrings.init() nao foi chamado - verifique TvApplication.onCreate"
        )
        return if (args.isEmpty()) ctx.getString(id) else ctx.getString(id, *args)
    }
}

/** Atalho de leitura para o call site: `str(R.string.canais)`. */
fun str(@StringRes id: Int, vararg args: Any): String = TvStrings.s(id, *args)
