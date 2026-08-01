import { cva, type VariantProps } from 'class-variance-authority';

export const loaderVariants = cva('', {
  variants: {
    uiSize: {
      default: 'size-6',
      sm: 'size-4',
      lg: 'size-8',
    },
  },
  defaultVariants: {
    uiSize: 'default',
  },
});
export type UiLoaderVariants = VariantProps<typeof loaderVariants>;
