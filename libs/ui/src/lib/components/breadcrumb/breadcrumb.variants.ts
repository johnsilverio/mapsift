import { cva, type VariantProps } from 'class-variance-authority';

export const breadcrumbVariants = cva('w-full', {
  variants: {
    uiSize: {
      sm: 'text-xs',
      md: 'text-sm',
      lg: 'text-base',
    },
  },
  defaultVariants: {
    uiSize: 'md',
  },
});
export type UiBreadcrumbSizeVariants = NonNullable<VariantProps<typeof breadcrumbVariants>['uiSize']>;

export const breadcrumbListVariants = cva(
  'text-muted-foreground flex flex-wrap items-center gap-1.5 wrap-break-word sm:gap-2.5',
  {
    variants: {
      uiAlign: {
        start: 'justify-start',
        center: 'justify-center',
        end: 'justify-end',
      },
      uiWrap: {
        wrap: 'flex-wrap',
        nowrap: 'flex-nowrap',
      },
    },
    defaultVariants: {
      uiAlign: 'start',
      uiWrap: 'wrap',
    },
  },
);
export type UiBreadcrumbAlignVariants = NonNullable<VariantProps<typeof breadcrumbListVariants>['uiAlign']>;
export type UiBreadcrumbWrapVariants = NonNullable<VariantProps<typeof breadcrumbListVariants>['uiWrap']>;

export const breadcrumbItemVariants = cva(
  'inline-flex items-center gap-1.5 transition-colors cursor-pointer hover:text-foreground last:text-foreground last:font-normal last:pointer-events-none',
);
export type UiBreadcrumbItemVariants = VariantProps<typeof breadcrumbItemVariants>;

export const breadcrumbEllipsisVariants = cva('flex', {
  variants: {
    uiColor: {
      muted: 'text-muted-foreground',
      strong: 'text-foreground',
    },
  },
  defaultVariants: {
    uiColor: 'muted',
  },
});
export type UiBreadcrumbEllipsisColorVariants = NonNullable<
  VariantProps<typeof breadcrumbEllipsisVariants>['uiColor']
>;
