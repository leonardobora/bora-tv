package io.github.leonardobora.boratv

import io.github.leonardobora.boratv.playlist.TvSavedItem
import io.github.leonardobora.boratv.playlist.TvSavedItemType

/** The original Home keeps recently watched live channels separate from VOD/series history. */
internal fun tvDashboardRecentLiveHistory(history: List<TvSavedItem>): List<TvSavedItem> =
    history.filter { it.itemType == TvSavedItemType.CHANNEL }
