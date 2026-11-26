# Motion Design & Lightweight 3D for a Premium, Calm, ADHD-Friendly Card-Stack PWA (2025–2026)

Scope: vanilla HTML/CSS/JS PWA, core interaction = fanned stack of task cards (swipe right = done, left = later), must run smoothly on iPhone Safari without libraries. Research date: 2026-11-26.

Method note: emilkowal.ski and rauno.me pages were read through a scraping proxy (Firecrawl) because direct fetch was blocked in this session. Some Emil Kowalski guidance comes from his published agent skill ("emil-design-eng" / "gestures"), listed at [tessl registry](https://tessl.io/registry/skills/github/emilkowalski/skill/emil-design-eng) and [skills.sh/emilkowalski](https://skills.sh/emilkowalski). It is a secondary source written by Emil, not a blog post, so treat it as his codified opinion.

## 1. Emil Kowalski & Rauno Freiberg: easing, durations, springs, interruptibility, when not to animate

### Takeaway
Motion should be fast (UI < 300 ms, sheets/drawers up to ~500 ms), use strong ease-out (never ease-in), animate only `transform`/`opacity`, stay interruptible (CSS transitions or springs, never keyframes on anything a gesture touches), and be removed from very frequent actions. For a calm, "elegant" brand feel, Sonner deliberately goes slightly slower with plain `ease` (400 ms), which matches a warm, high-end tone better than a snappy dev-tool feel.

### Cited Findings
**Speed and easing**
- "The best type of easing for this purpose is `ease-out`... Your animations should also usually be shorter than 300ms." Family's iOS app is cited as a perfect example of a snappy interface. — [Emil Kowalski, Great Animations](https://emilkowal.ski/ui/great-animations)
- Sonner's animation is "a bit slower than usual and uses `ease` as the easing type rather than `ease-out` to make it feel more elegant", matching the vibe of the whole library (cohesion). — [Great Animations](https://emilkowal.ski/ui/great-animations)
- Emil's token set: `--ease-out: cubic-bezier(0.23, 1, 0.32, 1)` (strong ease-out for UI), `--ease-in-out: cubic-bezier(0.77, 0, 0.175, 1)`, `--ease-drawer: cubic-bezier(0.32, 0.72, 0, 1)`. "Never use ease-in for UI animations." — [emil-design-eng skill](https://tessl.io/registry/skills/github/emilkowalski/skill/emil-design-eng)
- Duration table: button press feedback 100–160 ms; tooltips/small popovers 125–200 ms; dropdowns 150–250 ms; modals/drawers 200–500 ms; toasts use Sonner's 400 ms `ease`. — [emil-design-eng skill](https://tessl.io/registry/skills/github/emilkowalski/skill/emil-design-eng)
- Press feedback: `transform: scale(0.97)` on `:active` with `transition: transform 160ms var(--ease-out)`. Never enter from `scale(0)`; start at `scale(0.95)` + `opacity: 0` ("nothing in the real world appears from nothing"). — [emil-design-eng skill](https://tessl.io/registry/skills/github/emilkowalski/skill/emil-design-eng)
- Vaul (drawer) uses `cubic-bezier(0.32, 0.72, 0, 1)` over 500 ms, a curve taken from Ionic that closely matches iOS sheets. — [Building a drawer component](https://emilkowal.ski/ui/building-a-drawer-component)
- Small floating (non-edge) drawers should override to ~200 ms `cubic-bezier(0.165, 0.84, 0.44, 1)`; the 500 ms iOS timing only reads right on full-width edge sheets. — [gestures skill](https://skills.sh/emilkowalski)

**When NOT to animate (frequency rule)**
- Frequency table: 100+ times/day → no animation, ever; tens of times/day (hover, list navigation) → remove or drastically reduce; occasional (modals, drawers, toasts) → standard; rare/first-time (onboarding, celebrations) → can add delight. — [emil-design-eng skill](https://tessl.io/registry/skills/github/emilkowalski/skill/emil-design-eng)
- "Never animate keyboard initiated actions... Raycast has no animations and it feels right." — [Great Animations](https://emilkowal.ski/ui/great-animations)
- Rauno: when an interaction is executed hundreds of times a day "it does start to feel more like cognitive burden after seeing the same animation for the hundredth time"; "I removed motion from core interactions and suddenly felt like I was moving much faster." — [Rauno Freiberg, Invisible Details of Interaction Design](https://rauno.me/craft/interaction-design)

**Performance**
- Animate `transform` and `opacity` (composite only); `padding`/`margin` trigger layout+paint+composite. CSS/WAAPI animations stay smooth when the main thread is busy; rAF-based (Framer Motion) do not. Vercel fixed dropped frames by switching to CSS animations. — [Great Animations](https://emilkowal.ski/ui/great-animations)
- During drag, updating a CSS variable (`--swipe-amount`) on a parent recalculates styles for all children and drops frames; writing `transform: translateY(...)` directly on the dragged element fixed Vaul. — [Building a drawer component](https://emilkowal.ski/ui/building-a-drawer-component)

**Interruptibility**
- "A CSS transition can be interrupted and smoothly transition to a new value, even before the first transition has finished" (keyframes cannot). — [Great Animations](https://emilkowal.ski/ui/great-animations)
- Rauno: great interactions are modeled on real-world properties "like interruptability"; a thrown element should retain "the momentum and angle at which it was thrown... like how swiping a playing card would feel"; "Truly fluid gestures are immediately responsive." — [Rauno, Interaction Design](https://rauno.me/craft/interaction-design)
- Rauno on triggering: lightweight actions can trigger mid-swipe after some distance; to respond to intent, "triggering on gesture end, regardless of distance, feels right." Metaphors: horizontal swipe = pages of a book. — [Rauno, Interaction Design](https://rauno.me/craft/interaction-design)

**Springs in native CSS (2025)**
- Josh Comeau's "Springs and Bounces in Native CSS" (Oct 2025) uses `linear()` with sampled spring points to get spring motion in plain CSS transitions; a fixed duration is required (generators: Linear() Easing Generator, Easing Wizard). — [Josh W. Comeau, linear() timing function](https://joshwcomeau.com/animation/linear-timing-function); background: [A Friendly Introduction to Spring Physics](https://joshwcomeau.com/animation/a-friendly-introduction-to-spring-physics/) (2020 classic)
- Chrome docs: `linear()` can approximate bounce/spring; recommend a duration that fits the spring and an `@supports` fallback. — [Chrome: linear() easing](https://developer.chrome.com/docs/css-ui/css-linear-easing-function); [Chrome: Physics Based Easing](https://developer.chrome.com/docs/modern-web-guidance/guides/ui-behaviors/physics-based-easing)

### Inferences
- Recommended token set for this app: `--ease-out` (0.23,1,0.32,1) for taps/feedback, `--ease-sheet` (0.32,0.72,0,1) at 400–500 ms for sheets and card re-stacking, `ease` 400 ms for "soft, elegant" moments (toast, card arriving). That combination gives the warm/high-end feel without sluggishness.
- Swiping cards is the core, high-frequency action: keep the swipe itself crisp and short; reserve longer, decorative motion for rare events (finishing the whole stack, first-run).
- Because swipe release must be interruptible, implement release with CSS transitions (or a tiny JS spring), never `@keyframes`.

### Gaps
- animations.dev course content is paywalled; not reviewed directly.
- Exact Family app spring values are unpublished (Emil says he did not know them either — [Great Animations](https://emilkowal.ski/ui/great-animations)).

## 2. Best-in-class card-stack / swipe / deck interactions: physics, velocity, rubber-banding, re-stacking

### Takeaway
The proven pattern: 1:1 tracking while the finger is down (no easing), rotation proportional to horizontal offset (max ~15–20°), dismiss on distance (~40–50% of width) OR velocity (~0.11 px/ms in Sonner, ~300–500 px/s in libraries), release with a velocity-seeded spring/transition, fast snap-back if not thrown, rubber-band resistance at edges, and stack depth via small per-card scale/offset steps (Sonner: 5% scale per card).

### Cited Findings
**Sonner stacking and swipe (directly reusable for a fanned stack)**
- Stack formula: non-front toasts get `translateY(calc(var(--lift-amount) * var(--toasts-before)))` and `scale(calc((-1 * var(--toasts-before) * 0.05) + 1))` — i.e. each card behind is 5% smaller and lifted by a fixed amount. — [Building a toast component](https://emilkowal.ski/ui/building-a-toast-component)
- Dismiss rule: `velocity = Math.abs(swipeAmount) / timeTaken; if (Math.abs(swipeAmount) >= SWIPE_THRESHOLD || velocity > 0.11) removeToast()` — "0.11 is just a number that I ended up on through trial and error" (px/ms). — [Building a toast component](https://emilkowal.ski/ui/building-a-toast-component)
- Enter via transition, not keyframes: `transition: transform 400ms ease`, toggling `data-mounted` from `translateY(100%)` to `translateY(0)`, so new toasts can interrupt. — [Building a toast component](https://emilkowal.ski/ui/building-a-toast-component)

**Vaul drag details**
- Momentum-based dragging: "you don't need to drag until a certain point to close the drawer, you can just flick it." Dragging past the top is damped ("the more you drag, the less the drawer will move"). A 100 ms timeout after reaching scroll-top blocks accidental dismissals from fast scrolling. — [Building a drawer component](https://emilkowal.ski/ui/building-a-drawer-component)

**Gesture rules (Emil's gestures skill)**
- Two phases: TRACK (pointer down → position maps 1:1, no easing/duration/spring) and RELEASE (spring seeded with release velocity or CSS transition; never keyframes). — [gestures skill](https://skills.sh/emilkowalski)
- Rubber-band at edges (Motion `dragElastic ≈ 0.2`); dismiss on distance (~40–50% of travel) OR velocity; bounce only after a drag (0.1–0.3), zero bounce for button-triggered moves; fast snap-back; "an element dismisses in the direction it entered"; derive linked values (overlay opacity, background scale) from drag progress, not separate animations; `touch-action` on the drag axis; hit targets ≥ 44×44 px; gate hover behind `@media (hover: hover) and (pointer: fine)`; test on a real 120 Hz phone. — [gestures skill](https://skills.sh/emilkowalski)
- Under reduced motion, tracking stays (user produces it); momentum flings, bounce and decorative motion are reduced. — [gestures skill](https://skills.sh/emilkowalski)

**Tinder-like libraries (reference constants)**
- gajus/swing (vanilla, "as seen in Jelly and Tinder"): `throwOutConfidence = max(min(|x|/width,1), min(|y|/height,1))`; thrown out when confidence = 1; `maxRotation` default 20 (rotation = offset proportion × maxRotation); throw-out distance 450–500 px; transforms via CSS `transform`. — [gajus/swing](https://github.com/gajus/swing) (older classic, ~2014–2018)
- react-tinder-card: default "velocity" swipe requirement with threshold 300; "position" mode described as Tinder-like. solid-swipe-card default speed threshold 300 px/s. — [react-tinder-card README](https://cdn.jsdelivr.net/npm/react-tinder-card@1.6.4/readme.md); [search summary of solid-swipe-card](https://www.pkgstats.com/pkg:solid-swipe-card)
- Common component pattern: "Drag triggers rotation proportional to horizontal offset"; "Flick detection uses velocity threshold for snappy gestures." — [21st.dev Swipe Stack](https://21st.dev/@dev.yadhakim/components/swipe-stack)

### Inferences
- Concrete starting values for this PWA (tune on device): rotation = `clamp(-15°, dx / width * 15°, 15°)` with transform-origin at bottom center (playing-card feel); throw if `|dx| > 0.4 * width` or `|v| > 0.11 px/ms` (≈110 px/s… note Sonner's is measured as average over the whole drag, which is lower than instantaneous release velocity; library defaults of 300–500 px/s are on instantaneous velocity); throw-out continues along release vector with `transition: transform 300–400ms cubic-bezier(0.23,1,0.32,1)`; snap-back 250–300 ms with a slight `linear()` spring (bounce ≤ 0.2).
- Fanned stack: cards behind at `scale(1 - 0.05*i)`, `translateY(i * 8–12px)` and optionally `rotate(±1.5°*i)` alternating for a "hand of cards" feel; as the top card is dragged, interpolate the next card from its stacked position toward front (scale 0.95→1) using drag progress — this is the "linked values" rule and makes re-stacking feel continuous.
- Direction colour/label hint (e.g. warm sage "done" right, soft blush "later" left) should fade in with throwOutConfidence, so motion is not the only carrier of meaning.
- Use Pointer Events + `setPointerCapture`, `touch-action: pan-y` on the card (vertical page scroll still works), and write `style.transform` directly per `pointermove` inside rAF.
- Provide button/keyboard alternatives (✓ / later) that trigger the same throw with no bounce, per Emil's "no force applied → no bounce" rule.

### Gaps
- No primary source found for Tinder, Apple Wallet, Things 3, Arc, Linear or Family exact physics constants; none were published. Apple Wallet / Things 3 behaviours could not be verified from primary sources in this session.
- Vaul's own velocity threshold is not stated on the blog; the 0.11 number is from Sonner.

## 3. 3D / material motion trends on award sites and their iOS Safari performance

### Takeaway
2025 award-winning sites lean on GSAP + WebGL (e.g. Awwwards Site of the Year 2025, Lando Norris), but for a calm productivity PWA the transferable, library-free subset is: CSS 3D transforms (perspective, subtle tilt, flip), View Transitions for page/state changes (well supported in Safari 18+), and scroll-driven animations (Safari 26+). Main iOS pitfall: filters/backdrop-filter combined with `preserve-3d` render incorrectly or flatten 3D.

### Cited Findings
**Trends**
- "Motion becomes the norm: GSAP has been free since April 2025, Webflow Interactions run on GSAP"; Awwwards Site of the Year 2025 (Lando Norris) built with Webflow, GSAP, WebGL; immersive 3D via Spline or WebGL "holding its ground". — [Digidop, Web Design Trends 2026](https://www.digidop.com/blog/5-web-design-trends-2025) (secondary agency blog, not Awwwards itself)
- Tactile/soft depth returning ("making buttons feel truly clickable"); claymorphism listed as a 2025 trend without detail. — [Elementor 2025 trends](https://elementor.com/blog/2025-web-design-trends-best-practices/); [WP Engine 2025 trends](https://wpengine.com/blog/web-design-trends/) (secondary)

**View Transitions API support (key for state/page changes in vanilla JS)**
- Same-document `document.startViewTransition`: Safari 18. Cross-document (MPA) transitions: Safari 18.2, Chrome 126; opt-in via `@view-transition { navigation: auto; }`, same-origin only. — [Chrome: View Transitions](https://developer.chrome.com/docs/web-platform/view-transitions); [Chrome: cross-document](https://developer.chrome.com/docs/web-platform/view-transitions/cross-document)
- 2025 additions: `view-transition-class` (Safari 18, Firefox 144); `view-transition-name: match-element` (Safari 18.4, Chrome 137, Firefox 144); element-scoped transitions (Chrome 147, Safari 26.2); nested view-transition groups (Chrome 140, not Safari). — [Chrome: What's new in view transitions (2025)](https://developer.chrome.com/blog/view-transitions-in-2025)
- Conflicting data: `pagereveal` event listed as Safari 18.2 in one version and 26.2 in another of the Chrome page. — [Chrome: cross-document](https://developer.chrome.com/docs/web-platform/view-transitions/cross-document)

**Scroll-driven animations**
- Safari 26.0 "Added support for Scroll-driven Animations" (`animation-timeline: scroll()` / `view()`); the property must come after the `animation` shorthand. Accelerated scroll-driven animations run in the remote layer tree since Safari 26.3. Firefox still behind a flag in early 2026 → use `@supports`. — [WebKit Features in Safari 26.0](https://webkit.org/blog/17333/webkit-features-in-safari-26-0/); [WebKit: guide to scroll-driven animations](https://www.webkit.org/blog/17101/a-guide-to-scroll-driven-animations-with-just-css/); [Safari 27.3 release notes](https://developer.apple.com/documentation/safari-release-notes/safari-27_3-release-notes.md); [camoa guide](https://camoa.github.io/dev-guides/css/modern-css/scroll-driven-animations)

**CSS 3D on iOS Safari**
- WebKit bug: setting both a 3D transform and `backdrop-filter` on an element applies the blur incorrectly. — [WebKit Bug 252181](https://bugs.webkit.org/show_bug.cgi?id=252181)
- Filters (e.g. `drop-shadow`) on a wrapper flatten a `preserve-3d` flip card; move the filter to an outer wrapper or onto faces. — [css filter flattens 3d (2026)](https://kody-w.github.io/2026/04/26/css-filter-flattens-3d/)
- Motion docs: 3D transforms are among the most performance-friendly values in CSS, but `preserve-3d` doesn't guarantee children get projected. — [Motion: 3D transforms](https://motion.dev/docs/3d-transforms)
- Historical: `-webkit-overflow-scrolling: touch` broke 3D/perspective on iOS (old bug). — [WebKit Bug 140415](https://bugs.webkit.org/show_bug.cgi?id=140415) (older)
- Tilt technique reference (pointer-mapped `rotateX/rotateY` + radial-gradient glare layer). — [jvinhit: CSS 3D interactive tilt and parallax](https://jvinhit.github.io/blog/css-3d-03-interactive-tilt-and-parallax/)

### Inferences
- Good-fit 3D ideas for this app, all CSS-only:
  1. Fanned deck with `perspective: 1200px` on the stack and a tiny `rotateX(4–6deg)` so cards read as physical paper lying slightly back.
  2. Dragged card tilts in 3D (`rotateY` up to ~8° proportional to dx, plus 2D `rotateZ`) with a soft radial "sheen" pseudo-element whose position follows the pointer — light, not glossy, fits "warm, high-end".
  3. Card flip (`rotateY(180deg)`, `backface-visibility: hidden`) to reveal task details/subtasks, 400–500 ms sheet curve.
  4. View Transitions for navigating between Today stack ↔ task detail (shared-element morph of the card via `view-transition-name`), and for re-ordering/"later" pile changes. Safari 18+ covers same-document use.
  5. Scroll-driven subtle reveal for a history/"done today" list — only progressive enhancement behind `@supports (animation-timeline: view())`, disabled under reduced motion.
- Keep `backdrop-filter` (glass) off any element inside the 3D context; put shadows on a flat parent or use pre-blurred shadow layers (box-shadow on a sibling) to avoid flattening.
- WebGL/Three.js is not needed; if used at all, limit to a single, static-ish hero (e.g. ambient soft gradient blob on a celebration screen) and skip under reduced motion/low power.

### Gaps
- No 2025–2026 benchmark found for CSS 3D tilt/glare FPS on iPhone Safari; must be tested on device.
- No authoritative Awwwards/Godly SOTD list with motion breakdowns was retrieved (Awwwards pages not fetched); trend evidence is from secondary blogs.
- No reliable source found on a "soft clay 3D" web trend specifically.

## 4. ADHD-related motion guidance: reduced motion, distraction, reward/celebration, WCAG 2.3.3, vestibular safety

### Takeaway
WCAG 2.3.3 (AAA) asks that interaction-triggered non-essential motion can be disabled (sufficient technique: `prefers-reduced-motion`); Apple HIG says avoid motion on frequent interactions, keep feedback brief, make motion optional and cancelable. For ADHD, practitioner guidance favours calm, purposeful, non-repeating motion; completion celebrations are common in ADHD apps but no peer-reviewed evidence on their effect was found.

### Cited Findings
- WCAG 2.3.3 intent: "Users are not harmed or distracted by motion. Support user preferences for motion, and eliminate unnecessary motion effects." Applies to motion triggered by interaction (web-initiated motion falls under 2.2.2); essential animation exempt; parallax is a known vestibular trigger causing dizziness, nausea, headaches; sufficient technique C39 = `prefers-reduced-motion`. — [W3C Understanding SC 2.3.3](https://w3.org/WAI/WCAG21/Understanding/animation-from-interactions)
- Apple HIG Motion: "Add motion purposefully... Gratuitous or excessive animation can distract people"; "Aim for brevity and precision in feedback animations"; "In apps, generally avoid adding motion to UI interactions that occur frequently"; "Make motion optional... avoid using it as the only way to communicate important information"; "Strive for realistic feedback motion that follows people's gestures"; "Let people cancel motion... don't make people wait for an animation to complete." — [Apple HIG: Motion](https://developer.apple.com/design/human-interface-guidelines/motion)
- Emil: "Animations can make people feel sick or get distracted"; reduced-motion variant should swap movement for an opacity fade, e.g. `@media (prefers-reduced-motion: reduce) { .element { animation: fade 0.2s; } }`. — [Great Animations](https://emilkowal.ski/ui/great-animations)
- Emil's frequency table puts "celebrations" in the rare category where delight is allowed. — [emil-design-eng skill](https://tessl.io/registry/skills/github/emilkowalski/skill/emil-design-eng)
- ADHD-friendly UI guidance: honor Reduce Motion / Reduce Transparency; replace autoplay carousels with static content unless opted in; minimise distraction ("fewer competing elements, no aggressive motion or badges"). — [vp0: ADHD-Friendly Mobile App UI Guidelines](https://vp0.com/blogs/adhd-friendly-mobile-app-ui-guidelines) (practitioner blog)
- Decorative motion becomes a problem "when decorative movement repeats, starts without warning, or follows the user across the screen"; reduced-motion version can swap a spinning reward for a still image; motion must not be the only way information is conveyed. — [Editorialge: sensory-friendly app design](https://editorialge.com/?p=321071) (secondary)
- University guidance on designing for ADHD users (2025). — [St Andrews Digital Communications: Designing for users with ADHD](https://digitalcommunications.wp.st-andrews.ac.uk/2025/02/12/designing-for-users-with-adhd/)
- ADHD apps market surprise card-flip rewards/confetti on completion ("The surprise is what keeps you coming back") — marketing claims, not evidence. — [Focus Rewards: ADHD Pomodoro (App Store)](https://apps.apple.com/app/id6755358108)

### Inferences
- Reward design: per-card completion = small, brief, consistent feedback (≈200–300 ms: card flies off, a soft check glyph fades/scales 0.95→1 at the edge, optional haptic via `navigator.vibrate` where supported — note iOS Safari does not support Vibration API, so rely on visual). Bigger celebration only when the whole stack/daily goal is completed (rare → allowed), ≤ 1–1.5 s, non-looping, skippable by tap, never blocking the next action.
- Variable/“surprise” rewards may help engagement but risk distraction; offer a setting ("Celebrations: full / subtle / off") in addition to honoring `prefers-reduced-motion` — this also satisfies WCAG 2.3.3's "control to turn off non-essential animation".
- Reduced-motion mode for this app: keep 1:1 drag tracking (essential, user-produced), replace throw/rotation/bounce/fan-tilt with short opacity crossfades; disable View Transition morphs (`@media (prefers-reduced-motion) { ::view-transition-group(*) { animation: none } }`) and scroll-driven effects; no parallax anywhere.
- Avoid ambient/idle motion (breathing gradients, floating blobs, pulsing badges) on working screens — it competes for attention, which is the main ADHD risk.

### Gaps
- No peer-reviewed study found measuring whether confetti/reward animations help or hurt task completion for adults with ADHD; a 2025 Brazilian HCI paper on ADHD reward preferences surfaced only as an abstract ([JBCS](https://journals-sol.sbc.org.br/index.php/jbcs/article/download/5670/3964/39280)) and was not verified.
- iOS Safari Vibration API non-support stated from general knowledge, not verified in this session.
