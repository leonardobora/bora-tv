# IPTVnator Android TV port — licensing, legal & distribution decision memo

Scope: the experimental Google TV port in `android-tv/` (fork **Antaneyes/iptvnator**, branch `android-tv-port`, PR **#1699** to `4gray/iptvnator`, open/unmerged, author states it is unmaintained, Spanish-only and "vibe-coded"). Goal: your own TCL 55P8K and/or an Android TV box.

## 1. THE LICENCE BOUNDARY

| Situation | Trigger | Obligations |
|---|---|---|
| Build, sign, install on your own TV, modify freely | none (GPL §0/§2) | **Nothing.** No source offer, no notice duty. GPL obligations attach on *conveying*, not on private use. |
| Hand the APK (or a modified build) to another person — any binary conveyance | GPL-3.0 §6 | Give **complete corresponding source**: the whole `android-tv/` Gradle project incl. `build.gradle.kts`, `local.properties` template, proguard rules. Same licence (GPL-3.0-or-later), keep `LICENSE` + `NOTICE` verbatim, **mark your changes** with dates (§5a), add **no extra restrictions** (§10) — no "non-commercial", no DRM/anti-fork clause. |
| Public GitHub release or app store listing | §6 + branding | All of the above, plus a valid written offer where you ship binary only (§6d), and **trademark compliance** (see §2). Charging money is *allowed* by GPL — it doesn't change anything. |
| Ship it preinstalled inside a TV box you sell | GPL-3.0 §6 "Installation Information" | You must also supply whatever is needed to install the modified version on that device. Sideloading an APK you hand to someone does **not** trigger this. |

**Which directory is which:** upstream is MIT (`LICENSE.md`, © 2019–2026 4gray). `android-tv/` carries its own **GPL-3.0-or-later** `LICENSE`, and its `NOTICE` reprints the MIT notice plus a statement that the name/logo are covered by neither licence.

**MIT ↔ GPL mixing:** the port is a standalone Gradle project, outside the Nx workspace, sharing no code with the Angular/Electron app, and not in CI (port README; PR body). The only coupling is a *test* in the MIT tree (`playlist-backup.service.roundtrip.spec.ts`) asserting desktop import accepts the TV export shape — a file-format contract, not a code dependency, so neither side derives from the other. Gotchas: never copy `android-tv/` Kotlin into the MIT tree (an MIT repo can't ship GPL code *as* MIT; a merge of #1699 makes the repo mixed-licence per directory and the docs must say so); copying MIT code into your fork obliges you to keep the MIT notice and puts the combined work under GPL-3.0-or-later (MIT is GPL-compatible); and don't extend `TvDrm.kt` (ClearKey) into effective anti-modification DRM — GPL-3 §3/§6 dislikes it.

## 2. BRANDING

The port's README says the app name, application id (`com.iptvnator.googletv`) and branding are **placeholders** to be checked against `TRADEMARK.md` before publishing anywhere; the manifest uses label `IPTVnator TV`, `@drawable/ic_launcher`, `@drawable/tv_banner`, and **signs the release build with the local debug key** — so distribution needs your own key.

Upstream `TRADEMARK.md`: "IPTVnator" and the logo are **unregistered (common-law) trademarks** of 4gray; MIT covers the code only. You may **not** use "IPTVnator" or a confusingly similar variant ("IPTV-Nator", "IPTVNator"…) as your fork's name, store listing, paid product or service, may not reuse the logo/icon/artwork, and may not imply endorsement. You **may** factually say "based on IPTVnator" and **must** keep the MIT notice.

- **Personal build on your own TV:** "IPTVnator TV (unofficial build)" is a private, nominative label; the restriction bites on public listings, products and services. Fine for you, don't publish it that way.
- **Public build:** rename (own wordmark), own `applicationId` (not `com.iptvnator.googletv`), own icon + 320×180 banner, own signing key, README: "unofficial fork — IPTVnator code MIT © 4gray; `android-tv/` GPL-3.0-or-later".

## 3. DISTRIBUTION CHANNEL

- **Play Store (TV):** $25 Play Console account [fee unverified], TV form-factor opt-in, and the **TV app quality** checklist — launcher icon + banner, landscape without pillarboxing, no overscan clipping, and **TV-DP: fully navigable with the five-way D-pad** (developer.android.com/docs/quality-guidelines/tv-app-quality). The port's README calls **D-pad focus** its weakest area and it is Spanish-only with hard-coded strings, so it is unlikely to pass. Play's **IP policy** forbids apps that "encourage or induce infringement" and requires rights to all listing content — so `IPTVnator TV` / `com.iptvnator.googletv` is both an IP-policy problem and an explicit TRADEMARK.md violation (4gray points people at Google's trademark dispute channel). IPTV players also get DMCA'd in practice (Televizo has a live Play counter-notice thread), and nobody maintains this port. **Play is the wrong channel.**
- **GitHub Releases:** free, no review, installable via ADB or the TV's file/Downloader flow. Needs: own signing key, a tag, the GPL source offer pointing at the same tag, `LICENSE` + `NOTICE` present, README stating unofficial + GPL-3.0-or-later, own name/icon/banner.
- **Pure sideload:** `./gradlew assembleRelease` then `adb install -r app-release.apk` (README; use the release build — R8-minified, ~4 MB, faster on TV). Zero obligations while you keep it to yourself.

**Recommendation:** sideload privately now. If it earns its place, publish **signed APK + source on GitHub Releases under a new name**. Ignore Play unless someone (you) maintains it to TV quality standards.

## 4. LEGAL FRAMING

Installing your own APK on a TV you own: Android TV / Google TV supports ADB and file-based installs; Developer options is a normal supported setting on TCL Google TV and doesn't by itself void warranty — but TCL/Google terms don't promise support for third-party software, and damage your install causes is yours. In Brazil CDC art. 26 keeps coverage for defects unrelated to your modification; defects your modification caused aren't covered. Two source-level caveats: the manifest sets `usesCleartextTraffic="true"` and the release build is debug-key-signed — fine personally, not hardened.

Content: like upstream, the port **bundles no playlists, channels or subscriptions** — you point it at your own M3U/Xtream source, the same posture as TiviMate, Televizo and Jellyfin, and that is what keeps it legal. You cross the line by **bundling, curating, reselling or advertising pirate playlists** in or beside the build, or marketing the build as a way to get free channels: that is inducing infringement — exactly what Play's IP policy names and what triggers real DMCA actions on IPTV players. In Brazil, unauthorised pay-TV retransmission carries civil and criminal exposure (Lei 9.610/98; Lei 12.485/2011 on conditional access), and since any distributed build must be GPL + source-offered a pirate playlist has nowhere to hide anyway. Exactly where the Brazilian line falls is a lawyer's call, not mine.

## 5. ALTERNATIVES REALITY CHECK

| App | Licence | M3U | Xtream | XMLTV EPG | Catch-up | D-pad UI | On Google TV BR | Money | Updated | Biggest drawback |
|---|---|---|---|---|---|---|---|---|---|---|
| **TiviMate** (`ar.tvplayer.tv`) | proprietary | ✔ | ✔ | ✔ | ✔ | ✔✔ TV-native | Play + APK (tivimate.com/apk) | free tier + paid Premium | 2026 [exact ver. unverified] | closed source, paid; APK build has "fewer restrictions" |
| **OTT Navigator** | proprietary | ✔ | ✔ | ✔ | ✔ | ✔✔ highly configurable | Play/APK [listing unverified] | free + Pro | 2026 [unverified] | dense, poorly documented; freemium |
| **Televizo** (`com.ottplay.ottplay`) | proprietary | ✔ | ✔ | ✔ | ✔ | ✔ | Play | free **with ads** + Pro IAP | active | ads; has faced Play DMCA complaints |
| **Kodi + pvr.iptvsimple** | **GPL-2.0** (944★) | ✔ | ✘ no native XC login | ✔ | catch-up mode ✔ | ✔ but heavy, multi-screen | Kodi not on Play (kodi.tv/APK) | free | 2026-09-28 | no Xtream Codes login → no VOD/series, no auto-refresh metadata |
| **OwnTV** (`ahXN00/OwnTV`) | **GPL-3.0** (468★) | ✔ | ✔ | ✔ | ✔ | ✔✔ Compose for TV, remote-first | GitHub APK | free | 2026-09-28 | young, small user base, no desktop sibling |
| **Extreme-InfiniTV** | **GPL-3.0** (171★) | ✔ | ✔ | ✔ | ✔ | ✔ | GitHub APK | free | 2026-09-24 | small project, cross-platform compromises |
| **Jellyfin Android TV + ErsatzTV/Threadfin** | **GPL-2.0** | via server | via server | ✔ | ✔ | ✔✔ | Play (Jellyfin) | free, self-hosted | 2026-09-29 | you must run a server |

**Bottom line.** **Fork it if** you want one project across your IPTVnator desktop and the TV (the port's JSON backup is deliberately desktop-compatible and nothing above gives you that), or a no-ads, no-telemetry build you can change, or you already self-host the PWA and want the TV beside it, or you want the learning — fixing the focus layer is real, tractable work.

**Just use X if** the goal is "watch my channels on the TV tonight, cheaply": **TiviMate** (best out-of-box TV UX, paid), **OTT Navigator** (most configurable), or — the strongest reason not to fork — **OwnTV**, which already does M3U + Xtream + Stalker + EPG + catch-up on Android TV, is GPL-3.0, and was pushed 2026-09-28. Forking *this* port means inheriting a ~14,000-line unmaintained AI-generated `TvApp.kt`, Spanish-only hard-coded strings and an author-acknowledged broken focus layer. That is the price.

## 6. CITATIONS

Read directly:

- raw.githubusercontent.com/4gray/iptvnator/master/{LICENSE.md, TRADEMARK.md, README.md, AGENTS.md}
- raw.githubusercontent.com/Antaneyes/iptvnator/android-tv-port/android-tv/{LICENSE, NOTICE, README.md}, plus `app/src/main/AndroidManifest.xml` and `app/build.gradle.kts`
- `gh pr view 1699 --repo 4gray/iptvnator` · `gh api repos/Antaneyes/iptvnator/git/trees/android-tv-port?recursive=1`
- Play: `https://support.google.com/googleplay/android-developer/answer/9888072` (IP policy) · `https://developer.android.com/docs/quality-guidelines/tv-app-quality` · `https://developer.android.com/training/tv/publishing/distribute` · Televizo DMCA thread `https://support.google.com/googleplay/android-developer/thread/273513304`
- Alternatives: `https://tivimate.com/` · `https://play.google.com/store/apps/details?id=com.ottplay.ottplay` · `https://github.com/kodi-pvr/pvr.iptvsimple` · `https://github.com/ahXN00/OwnTV` · `https://github.com/infinitel8p/xtream` · `https://github.com/jellyfin/jellyfin-androidtv`
- Upstream warning on unofficial sites/subscriptions: `https://4gray.github.io/iptvnator/blog/beware-unofficial-iptvnator-websites/`
