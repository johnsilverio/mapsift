---
paths:
  - "apps/web/**/*.css"
  - "apps/web/**/*.scss"
  - "apps/web/**/*.html"
  - "libs/ui/**/*.css"
  - "libs/ui/**/*.scss"
  - "libs/ui/**/*.html"
---

# Design system checklist (PRD section 9, U1 to U12)

The UI contract. PRD section 9 is the authority and this file is the enforceable digest of it; where the two
disagree, the PRD wins. The visual identity was ratified by the owner from the throwaway prototype in
`tests/prototypes/editor`, and section 9 carries it in normative form.

## The prototype is a visual reference and nothing else

For design and interface work you are **expected to open the prototype** to see what the result must look
like. Three rules do not bend.

1. Always recreate by refactoring. No file, no class, no stylesheet block, no component structure moves
   across.
2. Where the prototype and PRD section 9 disagree, section 9 wins and the look is preserved by other means.
3. The permission covers appearance and interaction feel only. Architecture, state, persistence, identity,
   geometry and logic are governed by PRD Layers 2 and 3, and the prototype's shortcuts there are explicitly
   not inherited: client logic in the UI instead of the core, a browser key-value store instead of the
   storage interface, a counter instead of an operation log, a timestamp identifier instead of the
   collision-safe one, chrome hand-rolled around the component library, and a component that renders
   correctly only because of a mismatched theme block.

A visual comparison against the prototype is legitimate evidence that the rebuild matches the identity. Its
code is never cited as justification for a requirement, a structure, or a decision.

## U1, tokens are the single source of truth

- DO take every visual value from a named token. DON'T write a raw colour, radius, size, or spacing literal
  in a component; that is a lint failure, not a style opinion.
- The scales are closed and small on purpose: four radius steps, six type steps, four text steps, one accent
  plus its hover, divider and hairline, and one closed spacing scale. Adding a step is a change to the token
  file and is visible as such in review.
- Changing a token changes every surface with no component edited. If it does not, a component is carrying a
  literal.

## U2 and U3, one material

- There is **one glass material**: a single tint, a single blur, a single saturation. Surfaces differ only by
  alpha and elevation, never by colour. Three layers use it: chrome (top bar, rails, status bar), floating
  surface (panels), transient overlay (menus, pickers, dialogs, toasts, drag preview).
- **Inset content is solid and never blurred**: cards, fields, metric boxes, recessed wells. One card tone,
  one well tone, one hairline.
- A surface that invents its own blur, tint or saturation recipe is a defect, not a variation. That includes
  surfaces rendered outside the application root.
- Performance mode is a first-class mode applied at the document root, and it **removes the filter entirely**
  rather than blurring by zero. Both modes must hold contrast, and the N1 budgets are measured in both.

## U4 and U5, theme and type

- The chrome is dark by design; it is the identity, not a theme toggled off a light default. A component must
  never depend on a mismatched or default theme block to look right. A vendored component is mapped onto the
  Mapsift tokens when adopted, and if it cannot be mapped it is not adopted.
- Three families, one job each: sans for the interface, a display face for identity moments, monospace for
  data read character by character (SQL, coordinates, identifiers).
- **Tabular numerals globally.** This is a tool of numeric tables, and a metric that jitters as it updates is
  a metric the professional stops trusting.
- Never override the document root font size; the scales assume the standard root. The editor's base size
  lives on the editor host.

## U6 and U7, shell and panels

- The editor is a full-bleed map with the chrome floating over it: top bar, left tool rail, right panel dock,
  status bar, and a transparent stage between them. The stage is click-through so panning reaches the map
  through every gap, and each floating surface opts back into events for itself.
- The seam is a hairline frame with concave corners, and every shell dimension (44 px top bar, 48 px rails,
  26 px status bar, 4 px and 2 px seam radii) is a **token**, not a literal repeated per component.
- Every panel is the same surface with the same grab header and the same close control. Panels never overlap:
  a dragged panel is pushed out along the axis of least penetration, keeps a fixed gap, and stays clamped
  inside the stage.
- The map control cluster fades when a panel covers it rather than competing for the same pixels.

## U8 and U9, icons and states

- One icon set, line style, one stroke weight, sized from the scale. **No emoji as an interface affordance,
  ever.** An icon-only control always carries an accessible name and a tooltip.
- Interactive states are semantic tokens (hover, active, selected, disabled, focus, danger). DON'T name a
  class or token after a colour value.
- Hover is instant, with no transition. Focus is always visible. Selection is never conveyed by colour alone,
  and state is never conveyed by the accent hue alone.

## U10 and U11, the library and the map

- The chrome is built from `@mapsift/ui`, consumed **by package name**, never by a relative path into its
  source. If a primitive exists in the library, use it; if the library's version is not good enough, improve
  the library. No bespoke duplicate of a library primitive, and a primitive that turns out to be shared moves
  into the library rather than being copied a second time.
- The map is reached through a declarative component layer over MapLibre GL JS, built with the same technique
  and the same tokens. MapLibre's default chrome is suppressed in favour of Mapsift's controls.
- **No live map handle crosses a capability or core boundary.** The map components own the instance
  internally and expose serializable state outward. A reference project built on another renderer may inform
  the inventory and the API shape; its rendering backend does not come along.

## U12 and N7, catalog and accessibility

- Every library component appears in the versioned component catalog with its states. A component absent from
  the catalog fails review.
- Tokens are exported in a platform-neutral form, because the Angular library does not cross to Flutter but
  the identity must.
- The declared accessibility target is WCAG 2.2 level AA on the chrome: keyboard operability, visible focus,
  contrast, correct names and roles. The WebGL canvas is handled honestly through a declared non-visual path
  (the attribute table and inspection), never by pretending the canvas is accessible. A map-only affordance
  with no equivalent fails review.
- **To evaluate, not yet decided:** Angular's accessible component primitives package (Angular ARIA) was
  reported as promoted out of developer preview in the v22 release material (**reported, undated, and not surveyed**). It is a candidate for the
  `@mapsift/ui` primitives that carry the N7 burden (menu, dialog, listbox, tabs), and like every dependency
  it walks the external-dependency gate into `specs/dependencies.md` before adoption. Do not assume it is
  available or stable without confirming it there.
