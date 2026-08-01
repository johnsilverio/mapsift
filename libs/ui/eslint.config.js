// @ts-check
const { defineConfig } = require('eslint/config');
const rootConfig = require('../../eslint.config.js');

module.exports = defineConfig([
  ...rootConfig,
  {
    files: ['**/*.ts'],
    rules: {
      // This library follows the shadcn convention of applying a primitive as an attribute on a
      // native element (`<input ui-input />`), which keeps the native semantics and accessibility.
      // kebab-case is the majority style; the four directives still on camelCase are listed by
      // file below, so the debt stays countable rather than hidden behind a disabled rule.
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
      // Underscore marks a parameter that exists to satisfy a signature, which is most of the
      // ControlValueAccessor surface here.
      '@typescript-eslint/no-unused-vars': [
        'error',
        {
          argsIgnorePattern: '^_',
          varsIgnorePattern: '^_',
          caughtErrorsIgnorePattern: '^_',
        },
      ],
      // A library wrapping native elements must expose the native names.
      '@angular-eslint/no-input-rename': [
        'error',
        {
          allowedNames: ['aria-label', 'disabled'],
        },
      ],
    },
  },
  {
    // Removing a file from this list is how the selector migration is finished.
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
