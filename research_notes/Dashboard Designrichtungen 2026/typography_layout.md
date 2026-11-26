# Typography & Layout Directions 2025–2026 for a warm, feminine, high-end, ADHD-friendly productivity PWA (German UI)

Research date: 2026-11-26. 15 tool calls (Firecrawl search/scrape). Items I could not verify in this session are marked "(unverified)" and listed under Gaps.

## 1. Distinctive type systems vs. overused "AI-default" fonts

### Takeaway
2026 type trend writing stresses variable fonts and "contrast in character" (an expressive face paired with a deliberately plain one), and modern/soft serifs dominate premium lifestyle/beauty branding. Inter, Roboto, Open Sans, Lato, Arial and system fonts are named explicitly as generic defaults; but the "distinctive" alternatives recommended in widely copied AI prompt guides (Fraunces, Space Grotesk, Bricolage Grotesque, Satoshi, Clash Display, Newsreader) are themselves spreading fast, so they need unusual configuration (axes, scale, pairing) to stay non-generic.

### Cited Findings
**Trends**
- The Type Founders' 2026 trend piece: no single style defines 2026; recurring themes are "unexpected roles (bookish or text-oriented type used at surprising scales)", "contrast in character (expressive type paired with deliberately pragmatic type)", "more type as logo", and variable fonts "for both creative and performance reasons"; "restrained, almost basic, type is too" a trend — [The Type Founders](https://thetypefounders.com/world-of-type/typography-trends-in-2026/)
- Modern serif typography "continues to dominate premium branding", especially fashion, beauty, luxury and lifestyle — [DIN Studio, Oct 2026](https://din-studio.com/typography-trends-2026-styles-that-shape-modern-design/) (vendor blog selling serif fonts, so treat as weak evidence)
- Typewolf's "Top 10 most popular serif fonts" list (2026) is led by Ogg, Times New Roman, Caslon, Garamond, GT Super. These are mostly commercial, but they show where editorial taste sits: high-contrast display serifs and classic book faces — [Typewolf](https://www.typewolf.com/top-10-serif-fonts)

**Overused / "AI-default"**
- Anthropic's Claude Cookbook "Prompting for frontend aesthetics" tells models to avoid Arial, Inter, Roboto, Open Sans, Lato and system fonts. As alternatives it suggests: code (JetBrains Mono, Fira Code, Space Grotesk), editorial (Playfair Display, Crimson Pro, Fraunces), startup (Clash Display, Satoshi, Cabinet Grotesk), technical (IBM Plex, Source Sans 3), distinctive (Bricolage Grotesque, Obviously, Newsreader) — [Claude Cookbook](https://platform.claude.com/cookbook/coding-prompting-for-frontend-aesthetics)
- A published "Typography Expert" agent skill "explicitly retires the overused AI-design defaults (Inter, Roboto, Montserrat, Poppins, Fraunces, Geist, Söhne, the Fontshare/ITF starter…)". This shows the second-wave picks (Fraunces, Geist, Fontshare fonts) are already seen as clichés by some practitioners — [Skills Directory](https://www.skillsdirectory.com/skills/curiositech-typography-expert-windags-skills)
- Mainstream 2026 "best Google Fonts" listicles recommend "Fraunces + Inter" and Bricolage Grotesque as standard picks. That is evidence of saturation — [MadeGoodDesigns](https://madegooddesigns.com/best-google-fonts/); a social post calls Bricolage Grotesque "that humanized-AI feel" — [Facebook group post](https://www.facebook.com/groups/6612732138796326/posts/25820419284267657/)
- Space Grotesk is framed as a fintech/crypto/AI/developer-product font — [CSS Author](https://cssauthor.com/best-fonts-for-websites/)
- Figma's "24 best fonts for websites 2026" still lists Poppins, Raleway, Lora: the mainstream baseline to avoid if you want to look hand-crafted — [Figma](https://www.figma.com/resource-library/best-fonts-for-websites/)

**Verified font facts**
- **Fraunces** (Undercase Type): variable axes opsz 9–144, wght 100–900, SOFT 0–100, WONK 0–1; licence OFL-1.1; "a display, 'Old Style' soft-serif typeface inspired by the mannerisms of early 20th century typefaces such as Windsor, Souvenir, and the Cooper Series" — [GitHub undercasetype/Fraunces](https://github.com/undercasetype/Fraunces); OFL confirmed by [FindFont](https://www.findfont.co/font/fraunces)
- **Instrument Serif**: "a condensed display font designed for the Instrument brand", free on Google Fonts and GitHub. 17 uses on Fonts In Use, incl. German projects (Studio Böreck "Freedl Dolce Club"; Gemeinschaft Immanuel e.V. paired with Aeonik + JetBrains Mono) — [Fonts In Use](https://fontsinuse.com/typefaces/219915/instrument-serif); 20–21 websites catalogued (e.g. Hive, Munch, daikifujita.com, limestud.io) — [A1 Gallery](https://www.a1.gallery/font/instrument-serif), [save.design](https://save.design/fonts/instrument-serif); a common pairing is Inter + Instrument Serif — [One Page Love](https://onepagelove.com/typeface/instrument-serif)
- **General Sans** (Fontshare, designed by Frode Helland for ITF): 12 static + 2 variable (roman and italic), Extralight–Bold; supports German — [Fontshare](https://www.fontshare.com/fonts/general-sans)
- **Fontshare licence (ITF Free Font License)**: "100% free for personal and commercial use"; "You may self-host the Font Software on your own servers … for use on your own websites and applications, including through … CSS @font-face"; but no redistribution and no modification or derivative works without written consent (so no subsetting without consent) — [Fontshare ITF FFL](https://www.fontshare.com/licenses/itf-free-font-license). Note: the page now calls it a "Closed Source License". It is NOT open source, unlike OFL.

### Inferences
Proposed type systems for the app. Licence and download source are given for each. All Google Fonts are OFL unless stated. Only Fraunces' axes and General Sans' German support were verified above; the others are noted as needing a check.

1. **"Soft Editorial" (recommended default)**: Fraunces (headlines, big numerals; opsz high, SOFT 50–100, WONK 0) + a calm humanist/neo-grotesque body font that is not Inter, e.g. General Sans (Fontshare, ITF FFL, German verified) or an OFL alternative from Google Fonts. Why: the SOFT axis gives the warm, rounded, feminine 1970s feel without kitsch, and the setting is uncommon (most AI sites use Fraunces at default SOFT 0). Keep Fraunces out of body text and out of italics for ADHD readability.
2. **"Couture Condensed"**: Instrument Serif (display only: date headers like "Mittwoch, 26. November", card titles at 32px and up) + General Sans or Instrument Sans for UI. Instrument Serif has only Regular + Italic (my reading of its "condensed display font" description; check Google Fonts), so it should never carry UI text. Why: fashion-magazine elegance and narrow width, so long German compounds fit on cards.
3. **"Planner Paper"**: Newsreader or Literata (Google Fonts, OFL, variable with optical sizes, unverified here) for headings and numerals + a monospace accent (JetBrains Mono or IBM Plex Mono, OFL) for times and durations ("09:30", "25 Min"). Why: a stationery/planner metaphor where the monospace times are tabular, so the timeline aligns.
4. **"Single variable family" (lowest cognitive load, best for offline caching)**: one variable family for everything, with hierarchy made through weight and optical size only. Candidate: Fraunces is too ornate for body text, so a variable humanist sans is better (unverified options: Figtree, Onest, Atkinson Hyperlegible Next). One WOFF2 file is simplest to precache.
5. Avoid as primary voice: Inter, Roboto, Open Sans, Lato, Poppins, Montserrat, Space Grotesk, Bricolage Grotesque, and Fraunces + Inter used at default settings.

### Gaps
- I did not verify, in this session, the Google Fonts specimen data (axes, German glyph coverage, licence) for Newsreader, Literata, Instrument Sans, Figtree, Onest, Atkinson Hyperlegible Next, Satoshi, Geist, Manrope or Inter Tight. Any Latin-1 font should have ä ö ü ß, but check capital ẞ (U+1E9E) and „German quotes" before choosing.
- No Awwwards/Godly SOTD typography statistics were retrieved. "Award-winning site" usage is shown only through Fonts In Use / A1 Gallery catalogues.
- Pangram Pangram / Velvetyne licences were not checked. Pangram's free tier is commonly personal-use-only (unverified), so avoid it unless the licence is confirmed.

## 2. Editorial / print-inspired layout patterns in apps & dashboards

### Takeaway
Bento grids (modular tiles sized by importance, popularised by Apple) and oversized typography are the most widely documented 2025–2026 layout trends, and they are often combined. For an ADHD app, the useful parts are "one idea per tile" and "size = importance". Dense, decorative bento walls should be avoided.

### Cited Findings
- A bento grid "splits a webpage into a set of modular tiles or cards, and each tile is sized by how important its content is"; it is usually built on a 3×3 or 4×4 grid, and tiles "stack in a sensible order" on narrow screens; Apple uses bento in "keynotes, websites, product pages and manuals" — [Hoke Designs, Sep 2026](https://hokedesigns.com/bento-grids-oversized-typography-web-design-trends/)
- "Bento grids and oversized typography complement each other. The grid provides structure, and the type provides emphasis." Caveats: "Content comes first … Empty or filler tiles defeat the purpose"; oversized type needs strong contrast — [Hoke Designs](https://hokedesigns.com/bento-grids-oversized-typography-web-design-trends/)
- Bento named among the five defining UI trends of 2025, alongside liquid glass and blur — [VEXiON, Aug 2025](https://www.vexioncards.one/blog/ui-design-trends-2025); described as most effective for "dashboards, portfolios, and data-intensive websites" — [LinkedIn/Nilesh Mate](https://www.linkedin.com/pulse/emergence-bento-grids-uiux-trend-you-cant-afford-miss-nilesh-mate-nfsnc)
- The 2026 trend "unexpected roles: bookish or text-oriented type used at surprising scales" supports oversized serif numerals and dates as a design device — [The Type Founders](https://thetypefounders.com/world-of-type/typography-trends-in-2026/)

### Inferences
Concrete layout ideas for this app:
- **Desktop dashboard = "magazine cover + bento"**: a large serif date or greeting as the masthead ("Guten Morgen" / "Mi 26"), then a 3-column bento of 4–6 tiles max (Heute-Fokus, Nächster Termin, Energie, Streak). The biggest tile is the current task.
- **Hanging times (planner)**: times set in tabular monospace or tabular figures in a left gutter, outside the text column, like a printed agenda. The eye scans times vertically and titles stay left-aligned.
- **Oversized numerals**: count ("3 von 7"), timer ("24:59") or date in display serif at 64–120px. One per screen, as the single focal point.
- **Index-card metaphor for the swipe stack**: cream card with a subtle rule line, task title in display serif, metadata in small sans, one action per card. This matches the BDA "single colour background, no busy patterns" guidance (§3).
- **Mobile**: no bento. Use a single column and one card in focus, with a bottom nav of max 4–5 items. Bento tiles collapse into a vertical stack in priority order (as Hoke describes).
- Asymmetry is fine for whitespace, but avoid multi-column text (BDA, §3).

### Gaps
- I found no credible published case studies of editorial/bento layouts in productivity apps specifically (e.g. Things, Sunsama, Amie, Structured). Sources are generic trend blogs (low-to-medium authority, some likely AI-written). Primary Awwwards/Godly examples were not retrieved.

## 3. Readability guidance for ADHD / dyslexia-friendly UI

### Takeaway
The BDA Dyslexia Style Guide 2023 gives the most concrete numbers: 16–19px body text, line spacing 1.5, slightly increased letter spacing, headings at least 20% larger, left-aligned, no italics/underline/all caps, cream or pastel rather than white backgrounds, 60–70 character lines, single columns. Baymard/Ruder support 50–75 characters per line. I found no ADHD-specific typography research; ADHD guidance is mostly about reducing clutter and distraction (COGA).

### Cited Findings
**BDA Dyslexia Style Guide 2023**
- Source: [BDA Dyslexia Style Guide 2023, PDF mirror at BU](https://www.bumc.bu.edu/jmedday/files/2025/05/Dyslexia-Style-Guide-2023-BDA-Style-Guide-2023.pdf) (the text layer of this PDF is letter-shifted; decoded by me and cross-checked with the BDA's own summary: "Font size should be 12-14 point… Avoid underlining and italics - use bold for emphasis… Avoid text in uppercase/capital letters" — [BDA Facebook](https://www.facebook.com/bdadyslexia/posts/is-your-written-content-easy-for-everyone-to-readour-dyslexia-style-guide-shares/1513717897458113/))
  - Use sans serif fonts (Arial, Comic Sans; alternatives Verdana, Tahoma, Century Gothic, Trebuchet, Calibri, Open Sans)
  - Font size 12–14pt "or equivalent (e.g. 1–1.2em / 16–19 px)"
  - Larger letter spacing improves readability, "ideally around 35% of the average letter width"; excessive spacing reduces readability
  - Word spacing at least 3.5× letter spacing
  - Line spacing 1.5 (150%) preferable
  - Headings at least 20% larger than body; use bold for further emphasis
  - Avoid underlining and italics; use bold for emphasis
  - Avoid all caps for continuous text
  - Left-align without justification
  - Avoid multiple columns
  - Line length about 60–70 characters (the decoded wording reads oddly; treat as 60–70 chars)
  - Dark text on a light, not white, background; "White can appear too dazzling. Use cream or a soft pastel colour"
  - Single colour backgrounds, no patterns
  - Avoid green and red/pink combinations
  - Add extra space around headings and between paragraphs
- Line spacing of about 1.5 is the BDA standard recommendation — [Michaël Dardol guide](https://www.michaeldardol.com/opendyslexic-font-installer/guides/dyslexia-friendly-text-formatting/) (secondary)

**Line length**
- "The optimal line length for body text is 50–75 characters"; Ruder: 50–60 — [Baymard Institute](https://baymard.com/research-articles/line-length-readability). Baymard data reported second-hand: descriptions wider than 80 chars/line were skipped 41% more often than those at 60–70 — [Medium summary](https://medium.com/@wblekhoa/talk-aboutthe-optimal-length-of-text-in-ux-ui-525e689f0b71) (secondary, not verified on Baymard)
- NN/g: users won't read web content unless the text is clear, simple and easy to understand (legibility → readability → comprehension) — [NN/g](https://www.nngroup.com/articles/legibility-readability-comprehension/) (snippet only; no numbers retrieved)

**W3C COGA "Making Content Usable"**
- Lists "default fonts that are not clear or readable such as a cartoon font or gothic" as a failure example under "Support a Personalized and Familiar Interface" (Objective 8: Support Adaptation and Personalization) — [W3C COGA](https://www.w3.org/TR/coga-usable/)

### Inferences
Practical rules for this app:
- Body/UI text 17–18px on iPhone (iOS default body is 17pt) and 16–18px on desktop; line-height 1.5; letter-spacing +0.01 to +0.02em on body text (not 35% of letter width, which is extreme for UI); never negative tracking on small text.
- Max 4–5 type sizes (e.g. 13 caption / 17 body / 22 title / 32 section / 64+ hero numeral), each step at least 20% larger (BDA). Use weight for emphasis, not italics.
- The BDA prefers sans for running text, so serif display faces (Fraunces, Instrument Serif) go only on short, large strings (dates, titles, numerals), never paragraphs or button labels.
- No ALL-CAPS labels. Common "premium" uppercase eyebrow labels conflict with the BDA; use small-caps-free sentence case.
- Cream/warm off-white background (e.g. a #FAF6F0-type tone) instead of pure white. This fits both the warm premium look and the BDA guidance.
- `max-width: 65ch` for any longer text (notes, AI coaching messages).
- Offer a user setting for larger text, more spacing and a "plain font" toggle (COGA personalization objective).
- German specifics: long compounds ("Wochenrückblick", "Erinnerungseinstellungen") need `hyphens: auto` with `lang="de"`, or narrow display fonts. Avoid justified text.

### Gaps
- I found no peer-reviewed ADHD-specific typography studies. The BDA guidance is for dyslexia, which is often comorbid with ADHD. The COGA design-guide page scrape returned no typography-specific text, so detailed COGA spacing/font numbers were not extracted (COGA is mostly non-numeric).
- The NN/g article's specific recommendations and NN/g ADHD content were not retrieved.

## 4. Practical web implementation (variable fonts, font-display, offline PWA, text-wrap)

### Takeaway
Self-host WOFF2 (subset to Latin incl. German), precache via the service worker, and use one or two variable files. For an offline-first PWA, `font-display: swap` (or `optional` once fonts are precached) plus `size-adjust` fallbacks avoids layout shift. `text-wrap: balance` and `pretty` work as progressive enhancement; `pretty` is now in Safari/iOS 26 and Chromium but not Firefox.

### Cited Findings
- font-display table: block (2–3s block, infinite swap), swap (0ms block, infinite swap), fallback (100ms, 3s), optional (100ms, no swap). `optional` = no layout shift, but the web font may not be used if late; `swap` = fast text but a "jarring shift" — [web.dev Best practices for fonts](https://web.dev/articles/font-best-practices)
- Self-hosting vs third party: "On paper, using a self-hosted font should deliver better performance … In practice … less clear cut"; when self-hosting, apply subsetting and WOFF2 yourself — [web.dev](https://web.dev/articles/font-best-practices)
- WOFF2 compresses about 30% better than WOFF; "Use only WOFF2 and forget about everything else" (Bram Stein, Web Almanac 2022, older reference) — [web.dev](https://web.dev/articles/font-best-practices)
- `unicode-range` + subsetting reduce file size; Google Fonts subsets automatically and supports a `text` parameter; tools subfont / glyphhanger; "Always check the font licenses to confirm they allow subsetting and self-hosting" — [web.dev](https://web.dev/articles/font-best-practices)
- Preload caveats: it takes resources from others and ignores `unicode-range`; inline @font-face is often better — [web.dev](https://web.dev/articles/font-best-practices)
- Use `size-adjust` (fallback metric overrides) to reduce CLS — [web.dev](https://web.dev/articles/font-best-practices)
- Variable fonts: one file replaces many; biggest win for sites that use many weights/styles. @font-face syntax `format('woff2') tech('variations')` with weight ranges — [web.dev variable fonts](https://web.dev/articles/variable-fonts)
- `text-wrap: pretty`: Chrome/Edge 117+ (as `text-wrap`) / 130+ (as `text-wrap-style`), Safari and iOS Safari 26, Samsung 24+, Firefox no support — [MDN text-wrap](https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/Properties/text-wrap), [MDN text-wrap-style](https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/Properties/text-wrap-style); "Safari 26.0 adds support for text-wrap: pretty" — [WebKit blog](https://webkit.org/blog/17333/webkit-features-in-safari-26-0/)
- Mozilla criticises Blink's `pretty` as narrowly focused on preventing short last lines, sometimes making paragraphs worse — [mozilla/standards-positions #993](https://github.com/mozilla/standards-positions/issues/993)
- balance/pretty are "safe" progressive enhancements: unsupported browsers ignore them — [Håvard Brynjulfsen](https://www.havardbrynjulfsen.design/writing/simple-progressive-enhancements-in-css)

### Inferences
- **For the PWA**: download the OFL fonts (Google Fonts / GitHub), subset to Latin + Latin-1 + €„"–ẞ, self-host WOFF2, list them in the service-worker precache (Workbox `precacheAndRoute` or the existing SW). Do not rely on fonts.googleapis.com at runtime: offline first load and privacy (Google Fonts CDN and GDPR are a known German concern; legal detail not researched here).
- Fontshare fonts may be self-hosted, but their licence forbids modification, which arguably includes subsetting. Use their full files as provided, or prefer OFL fonts if subsetting is needed.
- Once fonts are precached, `font-display: optional` gives zero layout shift on repeat visits. Use `swap` + a `size-adjust`-tuned local fallback (e.g. Georgia for serif, system-ui for sans) for first load.
- CSS: `h1,h2,.card-title{ text-wrap: balance }`, `p{ text-wrap: pretty }`, `html{ hyphens:auto }` with `<html lang="de">`, `font-variant-numeric: tabular-nums` for times/timers, `font-optical-sizing:auto`, and Fraunces via `font-variation-settings:"SOFT" 100,"WONK" 0`.
- Keep total font payload to 2 variable files (display + text), plus at most a mono accent.

### Gaps
- No exact file sizes for the Fraunces / General Sans variable WOFF2 were retrieved.
- No source checked on the GDPR status of Google Fonts CDN use in Germany (the LG München 2022 ruling is commonly cited but was not verified here).
