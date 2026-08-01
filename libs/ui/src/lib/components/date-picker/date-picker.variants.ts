import { cva, type VariantProps } from 'class-variance-authority';

export const datePickerVariants = cva('', {
  variants: {
    uiSize: {
      xs: '',
      sm: '',
      default: '',
      lg: '',
    },
    uiType: {
      default: '',
      outline: '',
      ghost: '',
    },
  },
  defaultVariants: {
    uiSize: 'default',
    uiType: 'outline',
  },
});

export type UiDatePickerSizeVariants = NonNullable<VariantProps<typeof datePickerVariants>['uiSize']>;
