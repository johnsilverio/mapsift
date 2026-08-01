import { cva, type VariantProps } from 'class-variance-authority';

export const dividerVariants = cva('bg-border block', {
  variants: {
    uiOrientation: {
      horizontal: 'h-px w-full',
      vertical: 'w-px h-full inline-block',
    },
    uiSpacing: {
      none: '',
      sm: '',
      default: '',
      lg: '',
    },
  },
  defaultVariants: {
    uiOrientation: 'horizontal',
    uiSpacing: 'default',
  },
  compoundVariants: [
    {
      uiOrientation: 'horizontal',
      uiSpacing: 'sm',
      class: 'my-2',
    },
    {
      uiOrientation: 'horizontal',
      uiSpacing: 'default',
      class: 'my-4',
    },
    {
      uiOrientation: 'horizontal',
      uiSpacing: 'lg',
      class: 'my-8',
    },
    {
      uiOrientation: 'vertical',
      uiSpacing: 'sm',
      class: 'mx-2',
    },
    {
      uiOrientation: 'vertical',
      uiSpacing: 'default',
      class: 'mx-4',
    },
    {
      uiOrientation: 'vertical',
      uiSpacing: 'lg',
      class: 'mx-8',
    },
  ],
});

export type UiDividerVariants = VariantProps<typeof dividerVariants>;
