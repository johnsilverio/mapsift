import { cva, type VariantProps } from 'class-variance-authority';

export const carouselVariants = cva('overflow-hidden', {
  variants: {
    uiOrientation: {
      horizontal: '',
      vertical: 'h-full',
    },
    uiControls: {
      none: '',
      button: '',
      dot: '',
    },
  },
  defaultVariants: {
    uiOrientation: 'horizontal',
  },
});

export const carouselContentVariants = cva('flex', {
  variants: {
    uiOrientation: {
      horizontal: '-ml-4 mr-0.5',
      vertical: '-mt-4 flex-col',
    },
  },
  defaultVariants: {
    uiOrientation: 'horizontal',
  },
});

export const carouselItemVariants = cva('min-w-0 shrink-0 grow-0 basis-full', {
  variants: {
    uiOrientation: {
      horizontal: 'pl-4',
      vertical: 'pt-5',
    },
  },
  defaultVariants: {
    uiOrientation: 'horizontal',
  },
});

export const carouselPreviousButtonVariants = cva('absolute size-8 rounded-full', {
  variants: {
    uiOrientation: {
      horizontal: 'top-1/2 -left-12.5 -translate-y-1/2',
      vertical: '-top-12 left-1/2 -translate-x-1/2 rotate-90',
    },
  },
  defaultVariants: {
    uiOrientation: 'horizontal',
  },
});

export const carouselNextButtonVariants = cva('absolute size-8 rounded-full', {
  variants: {
    uiOrientation: {
      horizontal: 'top-1/2 -right-12 -translate-y-1/2',
      vertical: '-bottom-12 left-1/2 -translate-x-1/2 rotate-90',
    },
  },
  defaultVariants: {
    uiOrientation: 'horizontal',
  },
});

export type UiCarouselOrientationVariants = NonNullable<VariantProps<typeof carouselVariants>['uiOrientation']>;
export type UiCarouselControlsVariants = NonNullable<VariantProps<typeof carouselVariants>['uiControls']>;
