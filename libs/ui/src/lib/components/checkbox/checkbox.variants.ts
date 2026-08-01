import { cva, type VariantProps } from 'class-variance-authority';

export const checkboxVariants = cva(
  'cursor-[unset] peer appearance-none border transition shadow hover:shadow-md focus-visible:outline-none focus-visible:ring-4 focus-visible:ring-ring/50 disabled:cursor-not-allowed disabled:opacity-50',
  {
    variants: {
      uiType: {
        default: 'border-primary checked:bg-primary',
        destructive: 'border-destructive checked:bg-destructive',
      },
      uiSize: {
        default: 'size-4',
        lg: 'size-6',
      },
      uiShape: {
        default: 'rounded',
        circle: 'rounded-full',
        square: 'rounded-none',
      },
    },
    defaultVariants: {
      uiType: 'default',
      uiSize: 'default',
      uiShape: 'default',
    },
  },
);

export const checkboxLabelVariants = cva('cursor-[unset] text-current empty:hidden select-none', {
  variants: {
    uiSize: {
      default: 'text-base',
      lg: 'text-lg',
    },
  },
  defaultVariants: {
    uiSize: 'default',
  },
});

export type UiCheckboxShapeVariants = NonNullable<VariantProps<typeof checkboxVariants>['uiShape']>;
export type UiCheckboxSizeVariants = NonNullable<VariantProps<typeof checkboxVariants>['uiSize']>;
export type UiCheckboxTypeVariants = NonNullable<VariantProps<typeof checkboxVariants>['uiType']>;
