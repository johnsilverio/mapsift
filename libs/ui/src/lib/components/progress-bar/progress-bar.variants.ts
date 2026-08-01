import { cva, type VariantProps } from 'class-variance-authority';

export const containerProgressBarVariants = cva('w-full transition-all', {
  variants: {
    uiType: {
      default: 'bg-primary/20',
      destructive: 'bg-destructive/20',
      accent: 'bg-chart-1/20',
    },
    uiSize: {
      default: 'h-2',
      sm: 'h-3',
      lg: 'h-5',
    },
    uiShape: {
      default: 'rounded-full',
      square: 'rounded-none',
    },
    uiIndeterminate: {
      true: 'relative',
    },
  },

  defaultVariants: {
    uiType: 'default',
    uiSize: 'default',
    uiShape: 'default',
  },
});
export type UiProgressBarSizeVariants = NonNullable<VariantProps<typeof containerProgressBarVariants>['uiSize']>;

export const progressBarVariants = cva('h-full transition-all', {
  variants: {
    uiType: {
      default: 'bg-primary',
      destructive: 'bg-destructive',
      accent: 'bg-chart-1',
    },
    uiShape: {
      default: 'rounded-full',
      square: 'rounded-none',
    },
    uiIndeterminate: {
      true: 'absolute animate-[indeterminate_1.5s_infinite_ease-out]',
    },
  },
  defaultVariants: {
    uiType: 'default',
    uiShape: 'default',
  },
});
export type UiProgressBarTypeVariants = NonNullable<VariantProps<typeof progressBarVariants>['uiType']>;
export type UiProgressBarShapeVariants = NonNullable<VariantProps<typeof progressBarVariants>['uiShape']>;
