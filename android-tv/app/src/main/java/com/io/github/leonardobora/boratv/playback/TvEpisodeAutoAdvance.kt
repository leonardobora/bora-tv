package io.github.leonardobora.boratv.playback

internal fun shouldAutoAdvanceEpisode(
    autoPlayEnabled: Boolean,
    isLive: Boolean,
    isAudio: Boolean,
    hasNextEpisode: Boolean,
): Boolean = autoPlayEnabled && !isLive && !isAudio && hasNextEpisode
