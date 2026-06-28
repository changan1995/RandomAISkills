---
name: eu4-save-analysis
description: >-
  Parse Europa Universalis IV save data (especially Pdx-Unlimiter info-snapshot
  JSON files) into a tidy timeline, then visualize it as an EU4-cover-style war
  timeline or growth-curve chart (gold-on-dark, original heraldic shields, Chinese
  or English). Use this skill WHENEVER the user uploads .eu4 saves, Pdx-Unlimiter
  savegame folders, or info_*.json snapshot files, OR asks to analyze an EU4
  campaign's development/income/debt/wars over time, build a war-history timeline,
  make an EU4 video thumbnail/data panel from a save, or chart how a country grew.
  Trigger even if they just say "read my eu4 save", "做一个战争时间线", "分析这个存档", or
  paste a path under Pdx-Unlimiter/savegames/eu4. For ironman (EU4bin) saves, guide
  the user to download the official rakaly Linux binary and upload it, then melt to
  plaintext to read HRE reforms/imperial authority, provinces, and exact war dates.
  Handles the duplicate-filename gotcha automatically.
---

# EU4 Save Analysis & Timeline Visualization

Turn EU4 save data into clean timelines and EU4-cover-style visuals. Built for a
recurring workflow: Chinese-language EU4 YouTube content (campaign growth curves,
war-history timelines, data-panel thumbnails).

## What you can and cannot read

**Pdx-Unlimiter `info_*.json` (the easy, recommended input)** — a lightweight
per-snapshot summary. Contains: in-game date, player tag, ruler/heir, ducats
(cash + loans), manpower, stability, prestige, monarch powers (adm/dip/mil),
development (total + autonomy-adjusted), allies, wars (opponent tags), mods, dlcs,
version. This is enough for growth curves and war-history timelines.

**Raw `.eu4` saves** — a zip of `meta` + `gamestate` + `ai`.
- *Non-ironman*: text (`EU4txt`), parseable directly.
- *Ironman*: binary (`EU4bin`). Must be melted to plaintext first. See below.

### Melting an ironman save (the working method)

The token→name table needed to decode `EU4bin` is Paradox copyright and is NOT in
any public source repo, NOT downloadable in this sandbox (release binaries redirect
to `release-assets.githubusercontent.com`, which is blocked), and cannot be
reproduced. BUT: the official **rakaly** release binary has the token table
compiled into it, and the user can download it themselves and upload it here.

**So when you hit an `EU4bin` ironman save, tell the user to do this:**

1. Download the Linux build of rakaly from:
   https://github.com/rakaly/cli/releases/tag/v0.8.17
   → the file `rakaly-0.8.17-x86_64-unknown-linux-musl.tar.gz`
2. Upload that `.tar.gz` here (alongside the `.eu4` save).

Then melt it yourself:
```bash
tar xzf <uploaded rakaly tar.gz> -C /tmp/rk
chmod +x /tmp/rk/rakaly-*/rakaly
/tmp/rk/rakaly-*/rakaly melt --unknown-key stringify --format eu4 \
    -o /tmp/melted.eu4 /mnt/user-data/uploads/<save>.eu4
# result starts with EU4txt — full plaintext, ~40MB, now fully parseable
```
rakaly subcommands: `melt` (binary→plaintext), `json` (save→JSON), `watch`.
Use `--unknown-key stringify` so unknown tokens become readable strings instead of
erroring. The melted save is a normal `EU4txt` file: grep/parse it directly.

Note on copyright: the user downloading the official binary for their own use is
fine. Do NOT bundle the rakaly binary into a shared/public skill — that would
redistribute the embedded token table. Each user downloads it themselves.

**Alternatives if the user prefers not to download rakaly:** melt via **PDX Tools**
(pdx.tools, browser-local) and re-upload the melted save, OR — simplest for most
requests — just use the Pdx-Unlimiter `info_*.json` snapshots (no melting needed;
enough for growth curves and war timelines).

### Parsing the melted save (what to extract)

Once melted to `EU4txt`, you can read everything. Key blocks:
- **HRE**: find `\nempire={`, brace-match to its end. Inside: `emperor="TAG"`,
  `imperial_influence=<float>` (= imperial authority), `electors={ TAG TAG ... }`,
  and `passed_reform="<id>"` lines (order = pass order). Match reform ids against
  `references/hre_reforms.md`. NOTE: scope the empire block by brace-matching —
  a naive grep picks up `passed_reform` from unrelated systems (e.g. China's
  改土归流 `establish_gaituguiliu_decision`), so confirm reforms are INSIDE the
  empire block. Imperial authority is a live-computed value; the save stores only
  the current number, never a per-year growth rate.
- **Exact war dates**: each war's `history={}` block has the declaration date and
  every peace date — replaces the snapshot-bounded estimates from info files.
- **Provinces, armies, country detail**: all present in the melted gamestate.

**What needs a melted gamestate (NOT in info files):** HRE reforms / imperial
authority / electors, province-level data, army/navy detail, war scores, and exact
war declaration & peace dates. From info snapshots you can only give
snapshot-bounded *estimates* of war start/end. Say so plainly when asked.

## Critical gotchas (these WILL bite you)

1. **Duplicate filenames.** Pdx-Unlimiter names every snapshot's info file
   identically (`info_<samehash>.json`), one per UUID subfolder. A flat
   `Compress-Archive` zips 100+ files that all share that name, and unzip collapses
   them to ONE on extract. `scripts/extract_timeline.py` reads zip entries directly
   (by index, not filename) so it recovers all of them. Never trust a post-unzip
   file count from a flat zip.

2. **Collecting the files on Windows.** The info files live one level down, inside
   UUID folders under
   `…\Pdx-Unlimiter\savegames\eu4\<campaign-uuid>\<snapshot-uuid>\info_*.json`.
   A non-recursive or top-level-only filter misses them (it only catches
   `campaign.json`). Give the user this PowerShell that preserves folder structure
   to avoid the name collision:
   ```powershell
   cd "$env:USERPROFILE\OneDrive\Documents\Pdx-Unlimiter\savegames\eu4\<campaign-uuid>"
   $tmp="$env:TEMP\eu4pack"; Remove-Item $tmp -Recurse -Force -ErrorAction SilentlyContinue
   Get-ChildItem -Recurse -File -Filter *.json | Where-Object {$_.Name -notlike "campaign*"} | % {
     $rel=$_.FullName.Substring((Resolve-Path .).Path.Length+1)
     $t=Join-Path $tmp $rel; New-Item -ItemType Directory (Split-Path $t) -Force|Out-Null; Copy-Item $_.FullName $t }
   Compress-Archive "$tmp\*" "$env:USERPROFILE\Desktop\eu4_infos.zip" -Force
   ```
   (Even a flat zip works as input because the script handles the collision — but
   structured is safer and lets the user sanity-check the count.)

3. **War structure.** In info files, `wars.comps` is a list of wars; each war has
   `tags` = the list of OPPONENT countries (no attacker/defender split, no war
   name). Don't look for `attackers`/`defenders` — they're empty.

4. **CJK fonts.** PNG rendering needs Noto CJK at
   `/usr/share/fonts/opentype/noto/`. If missing: `apt-get install -y fonts-noto-cjk`.

5. **No EU4 flag art.** Never extract, fetch, or redistribute EU4 flag textures
   (Paradox copyright). Draw ORIGINAL heraldic shield color-blocks using historical
   tinctures. See `references/country_colors.md`.

## Workflow

### 1. Get the data in
- `.eu4` uploaded → unzip, check first 6 bytes of `gamestate`. `EU4bin` = ironman
  → melt with uploaded rakaly binary (see "Melting an ironman save" above), then
  parse the resulting `EU4txt`. `EU4txt` = parse directly.
- Zip of info JSONs or a folder → go straight to step 2.
- Only one snapshot → still works; you just get a single data point.

### 2. Extract the timeline
```bash
python scripts/extract_timeline.py <input.zip|dir|file.json> \
    --out /tmp/timeline.json --wars-out /tmp/wars.json
```
Prints a per-snapshot table (date, dev, cash, loans, prestige, stability, monarch
powers, ruler) and a snapshot-bounded war-history table, and saves both as JSON.
Read the printed output to narrate highlights (dev jumps, debt spikes, ruler
changes, which wars were vs great powers).

### 3. Build the war list for visuals
Map each war interval from `/tmp/wars.json` into a display dict (see
`scripts/render_war_timeline.py` docstring for the schema). For each war pick:
- `zh`: a readable campaign-style name (use the user's naming if they have one,
  e.g. "勃艮第假赛").
- `main`: opponent tag (first letter → shield). Override letter where the user
  expects it (Ottoman → "O", not "T").
- `enemies`: short subtitle of the opposing coalition.
- `tier`: 大 / 中 / 小 by opponent strength → drives right-side color + label.
- `c1`/`c2`: heraldic colors from `references/country_colors.md`.
Confirm the mapping with the user before rendering — naming and colors are personal
taste and they'll often want tweaks.

### 4a. Interactive web timeline (inline)
Use the visualizer with the gold-on-dark cover style. **Inline the war data array
directly into the `<script>`** — never leave a `REPLACE_…` placeholder; an
un-substituted placeholder is invalid JS and the whole widget silently fails to
render. (This is the #1 way the web version breaks.) Each row: original SVG shield
(party-per-pale, gold edge, tag letter), name + subtitle, year span, tier label,
click → `sendPrompt(...)` for war detail.

### 4b. PNG file (downloadable, for video/thumbnail)
```bash
python scripts/render_war_timeline.py /tmp/wars_display.json \
    --out /mnt/user-data/outputs/war_timeline.png \
    --title "奥地利 · 哈布斯堡战争史" \
    --eyebrow "EUROPA UNIVERSALIS IV · 铁人局" \
    --subtitle "1446 — 1485 · 共 12 场主要战争"
```
Then `present_files` the PNG. 1280px wide, supersampled ×2, gold-on-dark, original
heraldic shields. The PNG path is robust (pure Pillow, no JS) — prefer it when the
web widget gives trouble.

### 5. Growth-curve chart (optional)
For dev/income/debt over time, feed `/tmp/timeline.json` to a Chart.js line chart
(dev on one axis, loans on another) — again inline the points array, no
placeholders. Highlight dev jumps and debt spikes in the prose.

## Style defaults
Gold-on-dark "EU4 cover" look: bg `#140d05`, card `#20160a`, gold `#e8c34a`, cream
`#f5e7c0`, gold edge on shields. Chinese-first labels. Tier colors: 大 `#d4423e`,
中 `#d98a2b`, 小 `#7a8a5c`. Keep it cinematic but readable; the user iterates on
naming/colors, so show options and expect revisions.

## Files
- `scripts/extract_timeline.py` — info-snapshot → timeline.json + wars.json (handles
  zip filename collisions, ironman detection upstream).
- `scripts/render_war_timeline.py` — war list → EU4-cover-style PNG.
- `references/country_colors.md` — tags, Chinese names, heraldic c1/c2, tier rules.
- `references/hre_reforms.md` — HRE reform id table (classic + emperor_ variants),
  plus how to read emperor / imperial authority / electors from a melted save.
