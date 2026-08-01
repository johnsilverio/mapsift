import { cva, type VariantProps } from 'class-variance-authority';

import { mergeClasses } from '../../utils/merge-classes';

export const inputGroupVariants = cva(
  mergeClasses(
    'rounded-md flex px-3 items-stretch w-full',
    '[&_input[ui-input]]:border-0! [&_input[ui-input]]:bg-transparent! [&_input[ui-input]]:outline-none!',
    '[&_input[ui-input]]:ring-0! [&_input[ui-input]]:ring-offset-0! [&_input[ui-input]]:px-0!',
    '[&_input[ui-input]]:py-0! [&_input[ui-input]]:h-full! [&_input[ui-input]]:flex-1',
    '[&_textarea[ui-input]]:border-0! [&_textarea[ui-input]]:bg-transparent! [&_textarea[ui-input]]:outline-none!',
    '[&_textarea[ui-input]]:ring-0! [&_textarea[ui-input]]:ring-offset-0! [&_textarea[ui-input]]:px-0! [&_textarea[ui-input]]:py-0!',
    'min-w-0 has-[textarea]:flex-col has-[textarea]:p-3 has-[textarea]:h-auto border border-input',
    // focus state
    'has-[[data-slot=input-group-control]:focus-visible]:border has-[[data-slot=input-group-control]:focus-visible]:border-ring has-[[data-slot=input-group-control]:focus-visible]:ring-ring/50 has-[[data-slot=input-group-control]:focus-visible]:ring-[3px]',
  ),
  {
    variants: {
      uiSize: {
        sm: 'h-8',
        default: 'h-9',
        lg: 'h-10',
      },
      uiDisabled: {
        true: 'opacity-50 cursor-not-allowed',
        false: '',
      },
    },
    defaultVariants: {
      uiSize: 'default',
      uiDisabled: false,
    },
  },
);

export const inputGroupAddonVariants = cva(
  'items-center whitespace-nowrap font-medium text-muted-foreground transition-colors disabled:pointer-events-none disabled:opacity-50',
  {
    variants: {
      uiType: {
        default: 'justify-center',
        textarea: 'justify-start w-full',
      },
      uiSize: {
        sm: 'text-xs',
        default: 'text-sm',
        lg: 'text-base',
      },
      uiPosition: {
        before: 'rounded-l-md border-r-0',
        after: 'rounded-r-md border-l-0',
      },
      uiDisabled: {
        true: 'cursor-not-allowed opacity-50 pointer-events-none',
        false: '',
      },
      uiAlign: {
        block: 'flex',
        inline: 'inline-flex',
      },
    },
    defaultVariants: {
      uiAlign: 'inline',
      uiPosition: 'before',
      uiDisabled: false,
      uiSize: 'default',
    },
    compoundVariants: [
      {
        uiType: 'default',
        uiSize: 'default',
        class: 'h-8.5',
      },
      {
        uiType: 'default',
        uiSize: 'sm',
        class: 'h-7.5',
      },
      {
        uiType: 'default',
        uiSize: 'lg',
        class: 'h-9.5',
      },
      {
        uiType: 'textarea',
        uiPosition: 'before',
        class: 'mb-2',
      },
      {
        uiType: 'textarea',
        uiPosition: 'after',
        class: 'mt-2',
      },
    ],
  },
);

export const inputGroupInputVariants = cva(
  mergeClasses(
    'font-normal flex has-[textarea]:h-auto w-full items-center rounded-md bg-background ring-offset-background',
    'file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground',
    'focus-within:outline-none disabled:cursor-not-allowed disabled:opacity-50 transition-colors',
  ),
  {
    variants: {
      uiSize: {
        sm: 'h-7.5 px-0.5 py-0 text-xs',
        default: 'h-8.5 px-0.5 py-0 text-sm',
        lg: 'h-9.5 px-0.5 py-0 text-base',
      },
      uiHasAddonBefore: {
        true: 'border-l-0 rounded-l-none',
        false: '',
      },
      uiHasAddonAfter: {
        true: 'border-r-0 rounded-r-none',
        false: '',
      },
      uiDisabled: {
        true: 'cursor-not-allowed opacity-50',
        false: '',
      },
    },
    defaultVariants: {
      uiSize: 'default',
      uiHasAddonBefore: false,
      uiHasAddonAfter: false,
      uiDisabled: false,
    },
  },
);

export type UiInputGroupAddonAlignVariants = NonNullable<VariantProps<typeof inputGroupAddonVariants>['uiAlign']>;
export type UiInputGroupAddonPositionVariants = NonNullable<
  VariantProps<typeof inputGroupAddonVariants>['uiPosition']
>;
