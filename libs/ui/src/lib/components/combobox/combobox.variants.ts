import { cva, type VariantProps } from 'class-variance-authority';

export const comboboxVariants = cva('', {
  variants: {
    uiWidth: {
      default: 'w-50',
      sm: 'w-37.5',
      md: 'w-62.5',
      lg: 'w-87.5',
      full: 'w-full',
    },
  },
  defaultVariants: {
    uiWidth: 'default',
  },
});

export type UiComboboxWidthVariants = NonNullable<VariantProps<typeof comboboxVariants>['uiWidth']>;
