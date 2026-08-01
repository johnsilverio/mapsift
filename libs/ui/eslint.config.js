// @ts-check
const { defineConfig } = require('eslint/config');
const rootConfig = require('../../eslint.config.js');

module.exports = defineConfig([
  ...rootConfig,
  {
    files: ['**/*.ts'],
    rules: {
      // The prefix `ui` that the schematic guessed was right. The shapes were not, and they are
      // widened here deliberately rather than by silencing the rule.
      //
      // This library follows the shadcn convention, where a primitive is frequently applied as
      // an attribute on a native element (`<input ui-input />`, `<div ui-menu>`) instead of
      // replacing it with a custom tag. Keeping the native element keeps its semantics and its
      // accessibility, which is the whole reason the pattern exists (N7). So a component may be
      // an element or an attribute, and a directive attribute is kebab-case to match how it is
      // actually written in a template. Narrowing these back would not fix anything; it would
      // report a deliberate convention as errors.
      // kebab-case is the library's majority convention (7 directives against 4) and the
      // direction it was already moving, which `[ui-dropdown], [uiDropdown]` shows by carrying
      // both. The rule accepts exactly one style, so the four that have not migrated are listed
      // by name below rather than hidden behind a disabled rule: an enumerated exception is
      // countable and a disabled rule is not, and nobody can add a fifth without editing that
      // list. Finishing the migration is design-system work under PRD section 9, and it touches
      // a structural directive's template microsyntax, which is not a scaffold's call to make.
      '@angular-eslint/directive-selector': [
        'error',
        { type: 'attribute', prefix: 'ui', style: 'kebab-case' },
      ],
      '@angular-eslint/component-selector': [
        'error',
        {
          type: ['element', 'attribute'],
          prefix: 'ui',
          style: 'kebab-case',
        },
      ],
      // Underscore marks a parameter that exists to satisfy a signature and is deliberately
      // unused, which is most of the ControlValueAccessor surface in this library
      // (`registerOnChange`, `setDisabledState`). Without this the convention reads as nine
      // defects.
      '@typescript-eslint/no-unused-vars': [
        'error',
        {
          argsIgnorePattern: '^_',
          varsIgnorePattern: '^_',
          caughtErrorsIgnorePattern: '^_',
        },
      ],
      // Renaming an input is a real smell in an application. In a component library that wraps
      // native elements it is the opposite: the public name has to be the native one, so a
      // consumer writes `aria-label` and `disabled` rather than a house dialect. Only those two
      // names are allowed, so the smell is still caught everywhere else.
      '@angular-eslint/no-input-rename': [
        'error',
        {
          allowedNames: ['aria-label', 'disabled'],
        },
      ],
    },
  },
  {
    // The four directives still on the camelCase selector, named one by one so the debt is
    // countable. Removing a file from this list is how the migration is finished.
    files: [
      'libs/ui/src/lib/components/popover/popover.component.ts',
      'libs/ui/src/lib/components/tooltip/tooltip.ts',
      'libs/ui/src/lib/core/directives/id.directive.ts',
      'libs/ui/src/lib/core/directives/string-template-outlet/string-template-outlet.directive.ts',
    ],
    rules: {
      '@angular-eslint/directive-selector': 'off',
    },
  },
  {
    files: ['**/*.html'],
    rules: {},
  },
]);
