import { cva, type VariantProps } from 'class-variance-authority';

export type uiInputIcon = 'email' | 'password' | 'text';

export const inputVariants = cva('w-full', {
  variants: {
    uiType: {
      default:
        'flex rounded-md border px-4 font-normal border-input bg-transparent file:border-0 file:text-foreground file:bg-transparent file:font-medium placeholder:text-muted-foreground outline-none focus-visible:border-ring focus-visible:ring-ring/50 focus-visible:ring-[3px] disabled:cursor-not-allowed disabled:opacity-50',
      textarea:
        'flex pb-2 min-h-20 h-auto rounded-md border border-input bg-background px-3 py-2 text-base placeholder:text-muted-foreground outline-none focus-visible:border-ring focus-visible:ring-ring/50 focus-visible:ring-[3px] disabled:cursor-not-allowed disabled:opacity-50',
    },
    uiSize: {
      default: 'text-sm',
      sm: 'text-xs',
      lg: 'text-base',
    },
    uiStatus: {
      error: 'border-destructive focus-visible:ring-destructive',
      warning: 'border-yellow-500 focus-visible:ring-yellow-500',
      success: 'border-green-500 focus-visible:ring-green-500',
    },
    uiBorderless: {
      true: 'flex-1 bg-transparent border-0 outline-none focus-visible:ring-0 focus-visible:ring-offset-0 px-0 py-0',
    },
  },
  defaultVariants: {
    uiType: 'default',
    uiSize: 'default',
  },
  compoundVariants: [
    { uiType: 'default', uiSize: 'default', class: 'h-9 py-2 file:max-md:py-0' },
    { uiType: 'default', uiSize: 'sm', class: 'h-8 file:md:py-2 file:max-md:py-1.5' },
    { uiType: 'default', uiSize: 'lg', class: 'h-10 py-1 file:md:py-3 file:max-md:py-2.5' },
  ],
});

export type UiInputTypeVariants = NonNullable<VariantProps<typeof inputVariants>['uiType']>;
export type UiInputSizeVariants = NonNullable<VariantProps<typeof inputVariants>['uiSize']>;
export type UiInputStatusVariants = NonNullable<VariantProps<typeof inputVariants>['uiStatus']>;
