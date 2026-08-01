# @mapsift/ui

The shared UI component library for Mapsift, consumed by package name from `apps/web` and never by a relative path into `src` (PRD U10). Built on Angular with signals, standalone components, OnPush change detection, and Tailwind CSS v4.

> **Authority.** The design system this library implements is specified in `specs/PRD.md` section 9 (U1 to U12): the token system, the single glass material, the two appearance axes, and the rule that a component never carries a raw colour or a scheme-specific override. Where this README and section 9 disagree, section 9 wins.

Every component uses CVA (Class Variance Authority) for type-safe variant management and `mergeClasses` (clsx + tailwind-merge) for conflict-free class composition.

## Setup

Register the library provider in your `app.config.ts`:

```typescript
import { provideUi } from '@mapsift/ui';

export const appConfig: ApplicationConfig = {
  providers: [
    provideUi(),
    // ...other providers
  ],
};
```

`provideUi()` registers custom `EventManagerPlugin` instances for debounce, prevent, and stop event modifiers.

Your `styles.css` must include the OKLCH design tokens (light and dark), the `@theme inline` block, and `@plugin "tailwindcss-animate"`. The token set itself is specified in PRD section 9 (U1), and the two appearance axes in U3 and U4.

## Directory Structure

```
libs/ui/src/lib/
  components/      44 component directories
  core/            Directives (UiIdDirective, UiStringTemplateOutletDirective) and provideUi()
  services/        UiDarkMode service
  utils/           mergeClasses, number helpers
```

## Importing

All public API is exported from `@mapsift/ui`:

```typescript
import {
  UiButtonComponent,
  UiInputDirective,
  UiDialogService,
  mergeClasses,
} from '@mapsift/ui';
```

---

## Core Infrastructure

### provideUi()

Call once in `app.config.ts`. Registers `UiEventManagerPlugin` and `UiDebounceEventManagerPlugin` for custom template event modifiers.

### UiIdDirective

Selector: `[uiId]`

Generates unique IDs for accessibility attributes (aria-labelledby, aria-describedby). Used internally by many components.

| Input | Type | Default |
|-------|------|---------|
| `uiId` | `string` | `'ssr'` |

Access the generated ID via `directive.id()`.

### UiStringTemplateOutletDirective

Selector: `[uiStringTemplateOutlet]`

Renders either a plain string or a `TemplateRef`. Used internally by components that accept `string | TemplateRef` inputs.

| Input | Type | Default |
|-------|------|---------|
| `uiStringTemplateOutlet` | `string \| TemplateRef<void>` | required |
| `uiStringTemplateOutletContext` | `object` | `undefined` |

### mergeClasses(...inputs: ClassValue[]): string

Combines `clsx` and `tailwind-merge` to produce a single class string with Tailwind conflicts resolved. Every component uses this internally.

```typescript
import { mergeClasses } from '@mapsift/ui';

const classes = mergeClasses('px-4 py-2', condition && 'bg-primary', 'px-6');
// Result: 'py-2 bg-primary px-6' (px-4 overridden by px-6)
```

### Number Utilities

```typescript
import { clamp, roundToStep, convertValueToPercentage } from '@mapsift/ui';

clamp(150, [0, 100]);                 // 100
roundToStep(7.3, 0, 5);              // 5
convertValueToPercentage(50, 0, 200); // 25
```

### UiDarkMode Service

Injectable root service for theme management. Supports light, dark, and system modes. Persists preference to `localStorage` under key `'theme'` and applies the `dark` class to `<html>`.

```typescript
import { UiDarkMode } from '@mapsift/ui';

export class MyComponent {
  private darkMode = inject(UiDarkMode);

  ngOnInit() {
    this.darkMode.init();
  }

  toggle() {
    this.darkMode.toggleTheme();
  }

  get currentTheme() {
    return this.darkMode.themeMode(); // 'light' | 'dark'
  }
}
```

---

## Components

### Accordion

Expandable content panels. Supports single (one panel open at a time) or multiple mode.

**UiAccordionComponent** `ui-accordion`

| Input | Type | Default |
|-------|------|---------|
| `uiType` | `'single' \| 'multiple'` | `'single'` |
| `uiCollapsible` | `boolean` | `true` |
| `uiDefaultValue` | `string \| string[]` | `''` |

**UiAccordionItemComponent** `ui-accordion-item`

| Input | Type | Default |
|-------|------|---------|
| `uiTitle` | `string` | `''` |
| `uiValue` | `string` | `''` |

```html
<ui-accordion uiType="single">
  <ui-accordion-item uiTitle="Section 1" uiValue="s1">
    Content for section 1.
  </ui-accordion-item>
  <ui-accordion-item uiTitle="Section 2" uiValue="s2">
    Content for section 2.
  </ui-accordion-item>
</ui-accordion>
```

---

### Alert

Static notification banner with icon, title, and description.

**UiAlertComponent** `ui-alert`

| Input | Type | Default |
|-------|------|---------|
| `uiType` | `'default' \| 'destructive'` | `'default'` |
| `uiTitle` | `string \| TemplateRef` | `''` |
| `uiDescription` | `string \| TemplateRef` | `''` |
| `uiIcon` | `UiIcon \| TemplateRef` | auto |

```html
<ui-alert uiType="destructive" uiTitle="Error" uiDescription="Something went wrong." />
```

---

### Alert Dialog

Modal confirmation dialog. Created programmatically via `UiAlertDialogService`.

```typescript
import { UiAlertDialogService } from '@mapsift/ui';

private alertDialog = inject(UiAlertDialogService);

this.alertDialog.confirm({
  uiTitle: 'Are you sure?',
  uiDescription: 'This action cannot be undone.',
  uiOkText: 'Confirm',
  uiCancelText: 'Cancel',
  uiOkDestructive: true,
  uiOnOk: () => this.deleteRecord(),
});
```

The service also provides `warning()` and `info()` convenience methods. Returns `UiAlertDialogRef<T>` for imperative control.

| Config Option | Type | Default |
|---------------|------|---------|
| `uiTitle` | `string \| TemplateRef` | required |
| `uiDescription` | `string` | `''` |
| `uiContent` | `string \| TemplateRef \| Type` | `''` |
| `uiOkText` | `string \| null` | `'OK'` |
| `uiCancelText` | `string \| null` | `'Cancel'` |
| `uiOkDestructive` | `boolean` | `false` |
| `uiMaskClosable` | `boolean` | `true` |
| `uiClosable` | `boolean` | `true` |

---

### Avatar

Image with fallback text and optional status indicator.

**UiAvatarComponent** `ui-avatar`

| Input | Type | Default |
|-------|------|---------|
| `uiSrc` | `string \| SafeUrl` | `''` |
| `uiAlt` | `string` | `''` |
| `uiFallback` | `string` | `''` |
| `uiSize` | `'sm' \| 'default' \| 'md' \| 'lg' \| 'xl' \| number` | `'default'` |
| `uiShape` | `'circle' \| 'rounded' \| 'square'` | `'circle'` |
| `uiStatus` | `'online' \| 'offline' \| 'doNotDisturb' \| 'away'` | none |

**UiAvatarGroupComponent** `ui-avatar-group`

| Input | Type | Default |
|-------|------|---------|
| `uiOrientation` | `'horizontal' \| 'vertical'` | `'horizontal'` |

```html
<ui-avatar uiSrc="/photo.jpg" uiAlt="John" uiFallback="JS" uiStatus="online" />

<ui-avatar-group>
  <ui-avatar uiSrc="/a.jpg" uiFallback="A" />
  <ui-avatar uiSrc="/b.jpg" uiFallback="B" />
</ui-avatar-group>
```

Uses `NgOptimizedImage` for lazy loading. Falls back to initials text when the image fails to load.

---

### Badge

Small label for status or category.

**UiBadgeComponent** `ui-badge`

| Input | Type | Default |
|-------|------|---------|
| `uiType` | `'default' \| 'secondary' \| 'destructive' \| 'outline'` | `'default'` |
| `uiShape` | `'default' \| 'square' \| 'pill'` | `'default'` |

```html
<ui-badge uiType="destructive">Critical</ui-badge>
<ui-badge uiType="outline" uiShape="pill">Pending</ui-badge>
```

---

### Breadcrumb

Navigation trail with router integration.

**UiBreadcrumbComponent** `ui-breadcrumb`

| Input | Type | Default |
|-------|------|---------|
| `uiSize` | `'sm' \| 'md' \| 'lg'` | `'md'` |
| `uiAlign` | `'start' \| 'center' \| 'end'` | `'start'` |
| `uiWrap` | `'wrap' \| 'nowrap'` | `'wrap'` |
| `uiSeparator` | `string \| TemplateRef` | default chevron |

**UiBreadcrumbItemComponent** `ui-breadcrumb-item`

| Input | Type | Default |
|-------|------|---------|
| `routerLink` | `string[]` | `[]` |
| `queryParams` | `Params` | `undefined` |
| `fragment` | `string` | `undefined` |

```html
<ui-breadcrumb>
  <ui-breadcrumb-item [routerLink]="['/']">Home</ui-breadcrumb-item>
  <ui-breadcrumb-item [routerLink]="['/dossiers']">Dossiers</ui-breadcrumb-item>
  <ui-breadcrumb-item>Current</ui-breadcrumb-item>
</ui-breadcrumb>
```

---

### Button

Primary interactive element. Works on `<button>`, `<a>`, or as `<ui-button>`.

**UiButtonComponent** `ui-button, button[ui-button], a[ui-button]`

| Input | Type | Default |
|-------|------|---------|
| `uiType` | `'default' \| 'destructive' \| 'outline' \| 'secondary' \| 'ghost' \| 'link'` | `'default'` |
| `uiSize` | `'default' \| 'xs' \| 'sm' \| 'lg' \| 'icon' \| 'icon-xs' \| 'icon-sm' \| 'icon-lg'` | `'default'` |
| `uiShape` | `'default' \| 'circle' \| 'square'` | `'default'` |
| `uiFull` | `boolean` | `false` |
| `uiLoading` | `boolean` | `false` |
| `uiDisabled` | `boolean` | `false` |

```html
<button ui-button uiType="destructive" uiSize="sm">Delete</button>
<button ui-button uiType="outline" [uiLoading]="isSaving()">Save</button>
<a ui-button uiType="link" [routerLink]="['/details']">View details</a>
```

Auto-detects icon-only content via MutationObserver and adjusts padding accordingly.

---

### Button Group

Groups buttons with shared border treatment.

**UiButtonGroupComponent** `ui-button-group`

| Input | Type | Default |
|-------|------|---------|
| `uiOrientation` | `'horizontal' \| 'vertical'` | `'horizontal'` |

```html
<ui-button-group>
  <button ui-button uiType="outline">Left</button>
  <button ui-button uiType="outline">Center</button>
  <button ui-button uiType="outline">Right</button>
</ui-button-group>
```

---

### Calendar

Date selection grid with single, multiple, and range modes.

**UiCalendarComponent** `ui-calendar`

| Input | Type | Default |
|-------|------|---------|
| `uiMode` | `'single' \| 'multiple' \| 'range'` | `'single'` |
| `value` | `Date \| Date[] \| null` | `null` |
| `minDate` | `Date \| null` | `null` |
| `maxDate` | `Date \| null` | `null` |
| `disabled` | `boolean` | `false` |

| Output | Type |
|--------|------|
| `dateChange` | `CalendarValue` |

Implements **ControlValueAccessor**. Full keyboard navigation (arrows, Home, End, PageUp/PageDown).

```html
<ui-calendar uiMode="single" [(value)]="selectedDate" />
```

---

### Card

Container with optional header (title, description, action) and footer.

**UiCardComponent** `ui-card`

| Input | Type | Default |
|-------|------|---------|
| `uiTitle` | `string \| TemplateRef` | `undefined` |
| `uiDescription` | `string \| TemplateRef` | `undefined` |
| `uiAction` | `string` | `''` |
| `uiHeaderBorder` | `boolean` | `false` |
| `uiFooterBorder` | `boolean` | `false` |

| Output | Type |
|--------|------|
| `uiActionClick` | `void` |

```html
<ui-card uiTitle="Analysis Summary" uiDescription="Last updated 2 hours ago">
  <p>Main content goes here.</p>
  <div card-footer>
    <button ui-button uiType="outline">Export</button>
  </div>
</ui-card>
```

---

### Carousel

Embla-based carousel with horizontal/vertical orientation.

**UiCarouselComponent** `ui-carousel`

| Input | Type | Default |
|-------|------|---------|
| `uiOrientation` | `'horizontal' \| 'vertical'` | `'horizontal'` |
| `uiControls` | `'button' \| 'dot' \| 'none'` | `'button'` |
| `uiOptions` | `EmblaOptionsType` | `{ loop: false }` |
| `uiPlugins` | `EmblaPluginType[]` | `[]` |

| Output | Type |
|--------|------|
| `uiInited` | `EmblaCarouselType` |
| `uiSelected` | `void` |

```html
<ui-carousel uiControls="dot">
  <ui-carousel-content>
    <ui-carousel-item>Slide 1</ui-carousel-item>
    <ui-carousel-item>Slide 2</ui-carousel-item>
  </ui-carousel-content>
</ui-carousel>
```

---

### Checkbox

Form-integrated checkbox with visual variants.

**UiCheckboxComponent** `ui-checkbox`

| Input | Type | Default |
|-------|------|---------|
| `uiType` | `'default' \| 'destructive'` | `'default'` |
| `uiSize` | `'default' \| 'lg'` | `'default'` |
| `uiShape` | `'default' \| 'circle' \| 'square'` | `'default'` |
| `uiDisabled` | `boolean` | `false` |

| Output | Type |
|--------|------|
| `checkChange` | `boolean` |

Implements **ControlValueAccessor**.

```html
<ui-checkbox formControlName="acceptTerms">I accept the terms</ui-checkbox>
```

---

### Combobox

Searchable dropdown with popover, keyboard navigation, and grouped options.

**UiComboboxComponent** `ui-combobox`

| Input | Type | Default |
|-------|------|---------|
| `options` | `UiComboboxOption[]` | `[]` |
| `groups` | `UiComboboxGroup[]` | `[]` |
| `value` | `string \| null` | `null` |
| `placeholder` | `string` | `'Select...'` |
| `searchPlaceholder` | `string` | `'Search...'` |
| `emptyText` | `string` | `'No results found.'` |
| `searchable` | `boolean` | `true` |
| `disabled` | `boolean` | `false` |
| `uiWidth` | `'default' \| 'sm' \| 'md' \| 'lg' \| 'full'` | `'default'` |

| Output | Type |
|--------|------|
| `uiValueChange` | `string \| null` |
| `uiComboSelected` | `UiComboboxOption` |

Implements **ControlValueAccessor**. Wraps Popover + Command internally.

```typescript
options = signal<UiComboboxOption[]>([
  { value: 'sp', label: 'São Paulo' },
  { value: 'rj', label: 'Rio de Janeiro' },
]);
```

```html
<ui-combobox [options]="options()" [(value)]="selectedState" />
```

---

### Command

Filterable command palette with keyboard navigation. Used internally by Combobox.

**UiCommandComponent** `ui-command`

| Input | Type | Default |
|-------|------|---------|
| `size` | `'sm' \| 'default' \| 'lg' \| 'xl'` | `'default'` |

| Output | Type |
|--------|------|
| `uiCommandChange` | `UiCommandOption` |
| `uiCommandSelected` | `UiCommandOption` |

Sub-components: `UiCommandInputComponent`, `UiCommandListComponent`, `UiCommandOptionComponent`, `UiCommandOptionGroupComponent`, `UiCommandEmptyComponent`, `UiCommandDividerComponent`.

```html
<ui-command>
  <ui-command-input placeholder="Search commands..." />
  <ui-command-list>
    <ui-command-option-group uiLabel="Actions">
      <ui-command-option uiValue="save" uiLabel="Save" uiShortcut="Ctrl+S" />
      <ui-command-option uiValue="export" uiLabel="Export" uiIcon="download" />
    </ui-command-option-group>
    <ui-command-empty>No results found.</ui-command-empty>
  </ui-command-list>
</ui-command>
```

---

### Date Picker

Button that opens a Calendar popover for date selection.

**UiDatePickerComponent** `ui-date-picker`

| Input | Type | Default |
|-------|------|---------|
| `value` | `Date \| null` | `null` |
| `placeholder` | `string` | `'Pick a date'` |
| `uiFormat` | `string` | `'MMMM d, yyyy'` |
| `uiSize` | `'xs' \| 'sm' \| 'default' \| 'lg'` | `'default'` |
| `uiType` | `UiButtonTypeVariants` | `'outline'` |
| `minDate` | `Date \| null` | `null` |
| `maxDate` | `Date \| null` | `null` |
| `disabled` | `boolean` | `false` |

| Output | Type |
|--------|------|
| `dateChange` | `Date \| null` |

Implements **ControlValueAccessor**.

```html
<ui-date-picker [(value)]="selectedDate" uiFormat="dd/MM/yyyy" />
```

---

### Dialog

General-purpose modal. Created programmatically via `UiDialogService`.

```typescript
import { UiDialogService } from '@mapsift/ui';

private dialog = inject(UiDialogService);

const ref = this.dialog.create({
  uiTitle: 'Edit Property',
  uiContent: EditPropertyComponent,
  uiData: { propertyId: 123 },
  uiWidth: '600px',
  uiOkText: 'Save',
  uiCancelText: 'Discard',
});
```

Returns `UiDialogRef<T, R, U>` for closing, subscribing to results, or passing data to the content component.

| Config Option | Type | Default |
|---------------|------|---------|
| `uiTitle` | `string \| TemplateRef` | required |
| `uiDescription` | `string` | `''` |
| `uiContent` | `string \| TemplateRef \| Type` | `''` |
| `uiOkText` | `string \| null` | `'OK'` |
| `uiCancelText` | `string \| null` | `'Cancel'` |
| `uiOkDestructive` | `boolean` | `false` |
| `uiHideFooter` | `boolean` | `false` |
| `uiClosable` | `boolean` | `true` |
| `uiMaskClosable` | `boolean` | `true` |
| `uiWidth` | `string` | auto |

---

### Divider

Visual separator line.

**UiDividerComponent** `ui-divider`

| Input | Type | Default |
|-------|------|---------|
| `uiOrientation` | `'horizontal' \| 'vertical'` | `'horizontal'` |
| `uiSpacing` | `'none' \| 'default' \| 'lg'` | `'default'` |

```html
<ui-divider />
<ui-divider uiOrientation="vertical" />
```

---

### Dropdown

Overlay menu triggered by click or hover.

**UiDropdownDirective** `[ui-dropdown]`

| Input | Type | Default |
|-------|------|---------|
| `uiDropdownMenu` | `UiDropdownMenuContentComponent` | optional |
| `uiTrigger` | `'click' \| 'hover'` | `'click'` |
| `uiDisabled` | `boolean` | `false` |

**UiDropdownMenuItemComponent** `ui-dropdown-menu-item`

| Input | Type | Default |
|-------|------|---------|
| `variant` | `'default' \| 'destructive'` | `'default'` |
| `inset` | `boolean` | `false` |
| `disabled` | `boolean` | `false` |

```html
<button ui-button [ui-dropdown]="menu">Actions</button>

<ui-dropdown-menu #menu>
  <ui-dropdown-menu-content>
    <ui-dropdown-menu-item>Edit</ui-dropdown-menu-item>
    <ui-dropdown-menu-item variant="destructive">Delete</ui-dropdown-menu-item>
  </ui-dropdown-menu-content>
</ui-dropdown-menu>
```

Full keyboard navigation (arrows, Enter, Space, Escape, Home, End).

---

### Empty

Placeholder for empty states with icon, title, description, and action slots.

**UiEmptyComponent** `ui-empty`

| Input | Type | Default |
|-------|------|---------|
| `uiIcon` | `UiIcon` | none |
| `uiImage` | `string \| TemplateRef` | none |
| `uiTitle` | `string \| TemplateRef` | none |
| `uiDescription` | `string \| TemplateRef` | none |
| `uiActions` | `TemplateRef[]` | `[]` |

```html
<ui-empty
  uiIcon="search"
  uiTitle="No dossiers found"
  uiDescription="Try adjusting your search filters."
/>
```

---

### Form

Wrapper components for form field layout, labels, and validation messages.

**UiFormFieldComponent** `ui-form-field` wraps a form control with label and messages.

**UiFormLabelComponent** `ui-form-label`

| Input | Type | Default |
|-------|------|---------|
| `uiRequired` | `boolean` | `false` |

**UiFormControlComponent** `ui-form-control`

| Input | Type | Default |
|-------|------|---------|
| `errorMessage` | `string` | `''` |
| `helpText` | `string` | `''` |

**UiFormMessageComponent** `ui-form-message`

| Input | Type | Default |
|-------|------|---------|
| `uiType` | `'default' \| 'error' \| 'success' \| 'warning'` | `'default'` |

```html
<ui-form-field>
  <label ui-form-label [uiRequired]="true">Property name</label>
  <ui-form-control errorMessage="Name is required" helpText="Enter the farm name">
    <input ui-input formControlName="name" />
  </ui-form-control>
</ui-form-field>
```

---

### Icon

Renders Lucide icons by name or custom icon data.

**UiIconComponent** `ui-icon, [ui-icon]`

| Input | Type | Default |
|-------|------|---------|
| `uiType` | `UiIcon` (string name or `LucideIconData`) | required |
| `uiSize` | `'sm' \| 'default' \| 'lg' \| 'xl'` | `'default'` |
| `uiStrokeWidth` | `number` | `2` |
| `uiAbsoluteStrokeWidth` | `boolean` | `false` |

```html
<ui-icon uiType="check" uiSize="lg" />
<ui-icon uiType="alert-triangle" />
```

80+ predefined icon names available: `house`, `settings`, `check`, `x`, `arrow-right`, `download`, `search`, `plus`, `trash`, etc.

---

### Input

Directive applied to native `<input>` and `<textarea>` elements.

**UiInputDirective** `input[ui-input], textarea[ui-input]`

| Input | Type | Default |
|-------|------|---------|
| `uiSize` | `'sm' \| 'default' \| 'lg'` | `'default'` |
| `uiStatus` | `'error' \| 'warning' \| 'success'` | `undefined` |
| `uiBorderless` | `boolean` | `false` |
| `value` | `string` (model, two-way) | `''` |

Implements **ControlValueAccessor**.

```html
<input ui-input placeholder="Search..." uiSize="sm" />
<textarea ui-input uiStatus="error" formControlName="notes"></textarea>
```

---

### Input Group

Wraps an input with optional before/after addons and loading state.

**UiInputGroupComponent** `ui-input-group`

| Input | Type | Default |
|-------|------|---------|
| `uiAddonBefore` | `string \| TemplateRef` | `''` |
| `uiAddonAfter` | `string \| TemplateRef` | `''` |
| `uiAddonAlign` | `'inline' \| 'center' \| 'start' \| 'end'` | `'inline'` |
| `uiSize` | `'xs' \| 'sm' \| 'default' \| 'lg'` | `'default'` |
| `uiLoading` | `boolean` | `false` |
| `uiDisabled` | `boolean` | `false` |

```html
<ui-input-group uiAddonBefore="https://" uiAddonAfter=".com">
  <input ui-input placeholder="domain" />
</ui-input-group>
```

Syncs size and disabled state to the child input automatically via `effect()`.

---

### Kbd

Keyboard shortcut display.

**UiKbdComponent** `ui-kbd`

```html
<ui-kbd>Ctrl</ui-kbd> + <ui-kbd>S</ui-kbd>

<ui-kbd-group>
  <ui-kbd>Ctrl</ui-kbd>
  <ui-kbd>Shift</ui-kbd>
  <ui-kbd>P</ui-kbd>
</ui-kbd-group>
```

---

### Layout

Application shell with header, content, footer, and collapsible sidebar.

**LayoutComponent** `ui-layout`

| Input | Type | Default |
|-------|------|---------|
| `uiDirection` | `'auto' \| 'vertical' \| 'horizontal'` | `'auto'` |

**HeaderComponent** `ui-header`

| Input | Type | Default |
|-------|------|---------|
| `uiHeight` | `number` | `64` |

**SidebarComponent** `ui-sidebar`

| Input | Type | Default |
|-------|------|---------|
| `uiWidth` | `string \| number` | `200` |
| `uiCollapsedWidth` | `number` | `64` |
| `uiCollapsible` | `boolean` | `false` |
| `uiCollapsed` | `boolean` (model) | `false` |
| `uiReverseArrow` | `boolean` | `false` |
| `uiTrigger` | `TemplateRef \| null` | `null` |

| Output | Type |
|--------|------|
| `uiCollapsedChange` | `boolean` |

Sub-components: `ContentComponent` (`ui-content`), `FooterComponent` (`ui-footer`), `SidebarGroupComponent` (`ui-sidebar-group`), `SidebarGroupLabelComponent` (`ui-sidebar-group-label`).

```html
<ui-layout>
  <ui-sidebar [uiCollapsible]="true" [(uiCollapsed)]="isSidebarCollapsed">
    <ui-sidebar-group>
      <ui-sidebar-group-label>Menu</ui-sidebar-group-label>
      <!-- nav items -->
    </ui-sidebar-group>
  </ui-sidebar>
  <ui-layout>
    <ui-header [uiHeight]="56"><!-- toolbar --></ui-header>
    <ui-content><!-- main content --></ui-content>
    <ui-footer><!-- footer --></ui-footer>
  </ui-layout>
</ui-layout>
```

Auto-detects horizontal direction when a sidebar is present.

---

### Loader

Spinning indicator with configurable size.

**UiLoaderComponent** `ui-loader`

| Input | Type | Default |
|-------|------|---------|
| `uiSize` | `'sm' \| 'default' \| 'lg'` | `'default'` |

```html
<ui-loader uiSize="lg" />
```

Renders a 12-bar circular spinner animation.

---

### Menu

CDK-based menu with click or hover trigger. Supports context menus.

**UiMenuDirective** `[ui-menu]`

| Input | Type | Default |
|-------|------|---------|
| `uiMenuTriggerFor` | `TemplateRef` | required |
| `uiTrigger` | `'click' \| 'hover'` | `'click'` |
| `uiPlacement` | `UiMenuPlacement` | `'bottomLeft'` |
| `uiHoverDelay` | `number` | `100` |
| `uiDisabled` | `boolean` | `false` |

**UiMenuItemDirective** `button[ui-menu-item]`

| Input | Type | Default |
|-------|------|---------|
| `uiType` | `'default' \| 'destructive'` | `'default'` |
| `uiInset` | `boolean` | `false` |
| `uiDisabled` | `boolean` | `false` |

**UiContextMenuDirective** `[ui-context-menu]`

| Input | Type | Default |
|-------|------|---------|
| `uiContextMenuTriggerFor` | `TemplateRef` | required |

Sub-components: `UiMenuLabelComponent`, `UiMenuShortcutComponent`.

```html
<button [ui-menu]="menuTemplate" uiTrigger="click">Open menu</button>

<ng-template #menuTemplate>
  <ui-menu-content>
    <ui-menu-label>Actions</ui-menu-label>
    <button ui-menu-item>Edit</button>
    <button ui-menu-item uiType="destructive">Delete</button>
  </ui-menu-content>
</ng-template>
```

---

### Pagination

Page navigation with previous/next buttons and page numbers.

**UiPaginationComponent** `ui-pagination`

| Input | Type | Default |
|-------|------|---------|
| `uiPageIndex` | `number` (model, two-way) | `1` |
| `uiTotal` | `number` | `1` |
| `uiSize` | `UiButtonSizeVariants` | `'default'` |
| `uiDisabled` | `boolean` | `false` |

| Output | Type |
|--------|------|
| `uiPageIndexChange` | `number` |

```html
<ui-pagination [(uiPageIndex)]="currentPage" [uiTotal]="totalPages" />
```

---

### Popover

Floating content panel anchored to a trigger element. Used internally by Combobox and DatePicker.

**UiPopoverDirective** `[uiPopover]`

| Input | Type | Default |
|-------|------|---------|
| `uiContent` | `TemplateRef` | required |
| `uiTrigger` | `'click' \| 'hover' \| null` | `'click'` |
| `uiPlacement` | `UiPopoverPlacement` | `'bottom'` |
| `uiVisible` | `boolean` | `false` |
| `uiOverlayClickable` | `boolean` | `true` |

| Output | Type |
|--------|------|
| `uiVisibleChange` | `boolean` |

```html
<button ui-button [uiPopover] [uiContent]="popContent">Open</button>

<ng-template #popContent>
  <ui-popover>
    <p>Popover content here.</p>
  </ui-popover>
</ng-template>
```

Uses CDK Overlay with flexible positioning and auto-close on outside click.

---

### Progress Bar

Horizontal progress indicator with determinate and indeterminate modes.

**UiProgressBarComponent** `ui-progress-bar`

| Input | Type | Default |
|-------|------|---------|
| `progress` | `number` | `0` |
| `uiType` | `'default' \| 'destructive' \| 'accent'` | `'default'` |
| `uiSize` | `'default' \| 'sm' \| 'lg'` | `'default'` |
| `uiShape` | `'default' \| 'square'` | `'default'` |
| `uiIndeterminate` | `boolean` | `false` |

```html
<ui-progress-bar [progress]="uploadProgress()" uiType="accent" />
<ui-progress-bar [uiIndeterminate]="true" />
```

---

### Radio

Form-integrated radio button.

**UiRadioComponent** `ui-radio`

| Input | Type | Default |
|-------|------|---------|
| `name` | `string` | `'radio'` |
| `value` | `unknown` | `null` |
| `disabled` | `boolean` | `false` |

| Output | Type |
|--------|------|
| `radioChange` | `boolean` |

Implements **ControlValueAccessor**.

```html
<ui-radio name="priority" value="high" formControlName="priority">High</ui-radio>
<ui-radio name="priority" value="low" formControlName="priority">Low</ui-radio>
```

---

### Resizable

Draggable panel splitter with min/max constraints.

**UiResizableComponent** `ui-resizable`

| Input | Type | Default |
|-------|------|---------|
| `uiLayout` | `'horizontal' \| 'vertical'` | `'horizontal'` |
| `uiLazy` | `boolean` | `false` |

| Output | Type |
|--------|------|
| `uiResizeStart` | `UiResizeEvent` |
| `uiResize` | `UiResizeEvent` |
| `uiResizeEnd` | `UiResizeEvent` |

**UiResizablePanelComponent** `ui-resizable-panel`

| Input | Type | Default |
|-------|------|---------|
| `uiDefaultSize` | `number \| string` | auto |
| `uiMin` | `number \| string` | `0` |
| `uiMax` | `number \| string` | `100` |
| `uiCollapsible` | `boolean` | `false` |
| `uiResizable` | `boolean` | `true` |

**UiResizableHandleComponent** `ui-resizable-handle`

| Input | Type | Default |
|-------|------|---------|
| `uiWithHandle` | `boolean` | `false` |
| `uiDisabled` | `boolean` | `false` |

```html
<ui-resizable uiLayout="horizontal">
  <ui-resizable-panel [uiDefaultSize]="30" [uiMin]="20">
    Sidebar
  </ui-resizable-panel>
  <ui-resizable-handle [uiWithHandle]="true" />
  <ui-resizable-panel [uiDefaultSize]="70">
    Main content
  </ui-resizable-panel>
</ui-resizable>
```

Keyboard support: Arrow keys, Shift+Arrow (larger steps), Home, End, Enter/Space (collapse).

---

### Segmented

Segmented control (tab-like toggle).

**UiSegmentedComponent** `ui-segmented`

| Input | Type | Default |
|-------|------|---------|
| `uiOptions` | `SegmentedOption[]` | `[]` |
| `uiDefaultValue` | `string` | `''` |
| `uiSize` | `'sm' \| 'default' \| 'lg'` | `'default'` |
| `uiDisabled` | `boolean` | `false` |

| Output | Type |
|--------|------|
| `uiChange` | `string` |

Implements **ControlValueAccessor**.

```typescript
segmentOptions: SegmentedOption[] = [
  { value: 'map', label: 'Map' },
  { value: 'satellite', label: 'Satellite' },
  { value: 'hybrid', label: 'Hybrid' },
];
```

```html
<ui-segmented [uiOptions]="segmentOptions" uiDefaultValue="map" (uiChange)="onViewChange($event)" />
```

---

### Select

Dropdown selection with single and multi-select modes.

**UiSelectComponent** `ui-select`

| Input | Type | Default |
|-------|------|---------|
| `uiPlaceholder` | `string` | `'Select an option...'` |
| `uiMultiple` | `boolean` | `false` |
| `uiSize` | `'sm' \| 'default' \| 'lg'` | `'default'` |
| `uiValue` | `string \| string[]` (model) | `''` or `[]` |
| `uiDisabled` | `boolean` | `false` |
| `uiLabel` | `string` | `''` |
| `uiMaxLabelCount` | `number` | `1` |

| Output | Type |
|--------|------|
| `uiSelectionChange` | `string \| string[]` |

**UiSelectItemComponent** `ui-select-item`

| Input | Type | Default |
|-------|------|---------|
| `uiValue` | `string` | required |
| `uiDisabled` | `boolean` | `false` |

Implements **ControlValueAccessor**. Full keyboard navigation.

```html
<ui-select uiPlaceholder="Select state" formControlName="state">
  <ui-select-item uiValue="SP">São Paulo</ui-select-item>
  <ui-select-item uiValue="RJ">Rio de Janeiro</ui-select-item>
  <ui-select-item uiValue="MG">Minas Gerais</ui-select-item>
</ui-select>
```

---

### Sheet

Slide-in panel from any edge. Created programmatically via `UiSheetService`.

```typescript
import { UiSheetService } from '@mapsift/ui';

private sheet = inject(UiSheetService);

this.sheet.create({
  uiTitle: 'Filters',
  uiSide: 'right',
  uiSize: 'lg',
  uiContent: FilterPanelComponent,
  uiHideFooter: true,
});
```

| Config Option | Type | Default |
|---------------|------|---------|
| `uiTitle` | `string \| TemplateRef` | required |
| `uiDescription` | `string` | `''` |
| `uiContent` | `string \| TemplateRef \| Type` | `''` |
| `uiSide` | `'left' \| 'right' \| 'top' \| 'bottom'` | `'left'` |
| `uiSize` | `'default' \| 'sm' \| 'lg' \| 'custom'` | `'default'` |
| `uiWidth` | `string` | auto |
| `uiHeight` | `string` | auto |
| `uiOkText` | `string \| null` | `'OK'` |
| `uiCancelText` | `string \| null` | `'Cancel'` |
| `uiHideFooter` | `boolean` | `false` |
| `uiMaskClosable` | `boolean` | `true` |

---

### Skeleton

Loading placeholder with pulse animation.

**UiSkeletonComponent** `ui-skeleton`

Apply custom dimensions via class input:

```html
<ui-skeleton class="h-4 w-48" />
<ui-skeleton class="h-12 w-12 rounded-full" />
<ui-skeleton class="h-32 w-full" />
```

---

### Slider

Range input with keyboard and pointer support.

**UiSliderComponent** `ui-slider`

| Input | Type | Default |
|-------|------|---------|
| `uiMin` | `number` | `0` |
| `uiMax` | `number` | `100` |
| `uiStep` | `number` | `1` |
| `uiDefault` | `number` | `0` |
| `uiValue` | `number \| null` | `null` |
| `uiOrientation` | `'horizontal' \| 'vertical'` | `'horizontal'` |
| `uiDisabled` | `boolean` | `false` |

| Output | Type |
|--------|------|
| `uiSlideIndexChange` | `number` |

Implements **ControlValueAccessor**.

```html
<ui-slider [uiMin]="0" [uiMax]="500" [uiStep]="10" formControlName="distance" />
```

---

### Switch

Toggle switch for boolean state.

**UiSwitchComponent** `ui-switch`

| Input | Type | Default |
|-------|------|---------|
| `uiChecked` | `boolean` (model, two-way) | `true` |
| `uiType` | `'default' \| 'destructive'` | `'default'` |
| `uiSize` | `'default' \| 'sm' \| 'lg'` | `'default'` |
| `uiDisabled` | `boolean` | `false` |

Implements **ControlValueAccessor**.

```html
<ui-switch [(uiChecked)]="isActive" />
<ui-switch formControlName="notifications" uiSize="sm" />
```

---

### Table

Composable table built on native HTML elements with attribute selectors.

| Component | Selector |
|-----------|----------|
| `UiTableComponent` | `table[ui-table]` |
| `UiTableHeaderComponent` | `thead[ui-table-header]` |
| `UiTableBodyComponent` | `tbody[ui-table-body]` |
| `UiTableRowComponent` | `tr[ui-table-row]` |
| `UiTableHeadComponent` | `th[ui-table-head]` |
| `UiTableCellComponent` | `td[ui-table-cell]` |
| `UiTableCaptionComponent` | `caption[ui-table-caption]` |

**Table variants** (on `table[ui-table]`):

| Input | Type | Default |
|-------|------|---------|
| `uiType` | `'default' \| 'striped' \| 'bordered'` | `'default'` |
| `uiSize` | `'default' \| 'compact' \| 'comfortable'` | `'default'` |

```html
<table ui-table uiType="striped" uiSize="compact">
  <thead ui-table-header>
    <tr ui-table-row>
      <th ui-table-head>Name</th>
      <th ui-table-head>Status</th>
    </tr>
  </thead>
  <tbody ui-table-body>
    @for (property of properties(); track property.id) {
      <tr ui-table-row>
        <td ui-table-cell>{{ property.name }}</td>
        <td ui-table-cell>{{ property.status }}</td>
      </tr>
    }
  </tbody>
</table>
```

---

### Tabs

Tab group with content switching, scroll navigation, and orientation support.

**UiTabGroupComponent** `ui-tab-group`

| Input | Type | Default |
|-------|------|---------|
| `uiTabsPosition` | `'top' \| 'bottom' \| 'left' \| 'right'` | `'top'` |
| `uiActivePosition` | `'top' \| 'bottom' \| 'left' \| 'right'` | `'bottom'` |
| `uiShowArrow` | `boolean` | `true` |
| `uiScrollAmount` | `number` | `100` |
| `uiAlignTabs` | `'center' \| 'start' \| 'end'` | `'start'` |

| Output | Type |
|--------|------|
| `uiTabChange` | `{ index, label, tab }` |
| `uiDeselect` | `{ index, label, tab }` |

**UiTabComponent** `ui-tab`

| Input | Type | Default |
|-------|------|---------|
| `label` | `string` | required |

Public method: `selectTabByIndex(index: number)`.

```html
<ui-tab-group (uiTabChange)="onTabChange($event)">
  <ui-tab label="Overview">Overview content</ui-tab>
  <ui-tab label="Analysis">Analysis content</ui-tab>
  <ui-tab label="Documents">Documents content</ui-tab>
</ui-tab-group>
```

---

### Toast

Notification toasts. Wraps `ngx-sonner`. Place once in your root layout.

**UiToastComponent** `ui-toaster`

| Input | Type | Default |
|-------|------|---------|
| `position` | `'top-left' \| 'top-center' \| 'top-right' \| 'bottom-left' \| 'bottom-center' \| 'bottom-right'` | `'bottom-right'` |
| `duration` | `number` | `4000` |
| `visibleToasts` | `number` | `3` |
| `closeButton` | `boolean` | `false` |
| `richColors` | `boolean` | `false` |
| `expand` | `boolean` | `false` |
| `theme` | `'light' \| 'dark' \| 'system'` | `'system'` |

```html
<!-- app.component.html -->
<router-outlet />
<ui-toaster position="top-right" [closeButton]="true" />
```

Trigger toasts using the `toast` function from `ngx-sonner`:

```typescript
import { toast } from 'ngx-sonner';

toast.success('Property saved successfully');
toast.error('Failed to load dossier');
```

---

### Toggle

Pressable button that toggles between on/off states.

**UiToggleComponent** `ui-toggle`

| Input | Type | Default |
|-------|------|---------|
| `uiType` | `'default' \| 'outline'` | `'default'` |
| `uiSize` | `'sm' \| 'md' \| 'lg'` | `'md'` |
| `uiDefault` | `boolean` | `false` |
| `uiDisabled` | `boolean` | `false` |

| Output | Type |
|--------|------|
| `uiToggleChange` | `boolean` |
| `uiToggleClick` | `void` |
| `uiToggleHover` | `void` |

Implements **ControlValueAccessor**.

```html
<ui-toggle uiType="outline" (uiToggleChange)="onBoldToggle($event)">
  <ui-icon uiType="bold" />
</ui-toggle>
```

---

### Toggle Group

A set of toggles that work together in single or multiple selection mode.

**UiToggleGroupComponent** `ui-toggle-group`

| Input | Type | Default |
|-------|------|---------|
| `uiMode` | `'single' \| 'multiple'` | `'multiple'` |
| `uiType` | `'default' \| 'outline'` | `'default'` |
| `uiSize` | `'sm' \| 'md' \| 'lg'` | `'md'` |
| `items` | `UiToggleGroupItem[]` | `[]` |
| `disabled` | `boolean` | `false` |

| Output | Type |
|--------|------|
| `valueChange` | `string \| string[]` |

Implements **ControlValueAccessor**.

```typescript
interface UiToggleGroupItem {
  value: string;
  label?: string;
  icon?: UiIcon;
  disabled?: boolean;
}
```

```html
<ui-toggle-group
  uiMode="single"
  [items]="alignOptions"
  formControlName="textAlign"
/>
```

---

### Tooltip

Hoverable or clickable hint anchored to an element.

**UiTooltipDirective** `[uiTooltip]`

| Input | Type | Default |
|-------|------|---------|
| `uiTooltip` | `string \| TemplateRef \| null` | `null` |
| `uiPosition` | `'top' \| 'bottom' \| 'left' \| 'right'` | `'top'` |
| `uiTrigger` | `'click' \| 'hover'` | `'hover'` |
| `uiShowDelay` | `number` | `150` |
| `uiHideDelay` | `number` | `100` |

| Output | Type |
|--------|------|
| `uiShow` | `void` |
| `uiHide` | `void` |

```html
<button ui-button uiTooltip="Save changes" uiPosition="bottom">
  <ui-icon uiType="save" />
</button>
```

Uses CDK Overlay for positioning. Automatically manages ARIA attributes.

---

### Tree

Hierarchical data display with expand/collapse, selection, checkboxes, and optional virtual scroll.

**UiTreeComponent** `ui-tree`

| Input | Type | Default |
|-------|------|---------|
| `uiData` | `TreeNode<T>[]` | `[]` |
| `uiSelectable` | `boolean` | `false` |
| `uiCheckable` | `boolean` | `false` |
| `uiExpandAll` | `boolean` | `false` |
| `uiVirtualScroll` | `boolean` | `false` |
| `uiVirtualItemSize` | `number` | `32` |

| Output | Type |
|--------|------|
| `uiNodeClick` | `TreeNode<T>` |
| `uiNodeExpand` | `TreeNode<T>` |
| `uiNodeCollapse` | `TreeNode<T>` |
| `uiSelectionChange` | `TreeNode<T>[]` |
| `uiCheckChange` | `TreeNode<T>[]` |

Custom content via `#nodeTemplate`:

```typescript
interface TreeNode<T> {
  key: string;
  label: string;
  data?: T;
  icon?: string;
  children?: TreeNode<T>[];
  expanded?: boolean;
  selected?: boolean;
  checked?: boolean;
  disabled?: boolean;
  leaf?: boolean;
}
```

```html
<ui-tree
  [uiData]="treeData()"
  [uiCheckable]="true"
  (uiCheckChange)="onCheckedChange($event)"
>
  <ng-template #nodeTemplate let-node>
    <ui-icon [uiType]="node.icon" uiSize="sm" />
    {{ node.label }}
  </ng-template>
</ui-tree>
```

Full keyboard navigation: Arrow keys for navigation, Enter to activate, Space for checkbox, Home/End for first/last.

Internal `UiTreeService` manages expand, select, and check state with tri-state checkbox propagation (parent/child).

---

## Components with ControlValueAccessor

These components integrate with Angular Reactive Forms via `formControlName` or `[(ngModel)]`:

| Component | Notes |
|-----------|-------|
| Calendar | Single, multiple, or range date selection |
| Checkbox | Boolean toggle |
| Combobox | String value from filtered options |
| Command | Selected command option |
| Date Picker | Single date via calendar popover |
| Input | Text value (string) |
| Radio | Value from radio group |
| Segmented | String value from segmented options |
| Select | String or string[] (multi-select) |
| Slider | Numeric value with step |
| Switch | Boolean toggle |
| Toggle | Boolean toggle |
| Toggle Group | String or string[] depending on mode |

## Component Patterns

**Variant styling**: Every component uses CVA. Pass variant inputs like `uiType`, `uiSize`, `uiShape` to control appearance. Custom classes are always mergeable via the `class` input.

**Template flexibility**: Components that accept `uiTitle`, `uiDescription`, `uiContent`, etc. typically accept both `string` and `TemplateRef<void>`, giving you full control over complex content.

**Service-driven modals**: Dialog, AlertDialog, and Sheet are created via injectable services (`UiDialogService`, `UiAlertDialogService`, `UiSheetService`). They return ref objects for imperative control.

**Composition over configuration**: Table, Command, Breadcrumb, and other multi-part components use child components instead of complex config objects. Import and compose them in your template.

**Accessibility**: All interactive components include ARIA attributes, keyboard navigation, and focus management. Tree, Command, Select, and Combobox have full keyboard support.
