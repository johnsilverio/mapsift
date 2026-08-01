import { cva, type VariantProps } from 'class-variance-authority';

export const avatarVariants = cva(
  'relative flex flex-row items-center justify-center box-content cursor-default bg-muted',
  {
    variants: {
      uiSize: {
        sm: 'size-8',
        default: 'size-10',
        md: 'size-12',
        lg: 'size-14',
        xl: 'size-16',
      },
      uiShape: {
        circle: 'rounded-full',
        rounded: 'rounded-md',
        square: 'rounded-none',
      },
    },
    defaultVariants: {
      uiSize: 'default',
      uiShape: 'circle',
    },
  },
);

export const imageVariants = cva('relative object-cover object-center w-full h-full z-10', {
  variants: {
    uiShape: {
      circle: 'rounded-full',
      rounded: 'rounded-md',
      square: 'rounded-none',
    },
  },
  defaultVariants: {
    uiShape: 'circle',
  },
});

export const avatarGroupVariants = cva('flex items-center [&_img]:ring-2 [&_img]:ring-background', {
  variants: {
    uiOrientation: {
      horizontal: 'flex-row -space-x-3',
      vertical: 'flex-col -space-y-3',
    },
  },
  defaultVariants: {
    uiOrientation: 'horizontal',
  },
});

export type UiAvatarVariants = VariantProps<typeof avatarVariants>;
export type UiImageVariants = VariantProps<typeof imageVariants>;
export type UiAvatarGroupVariants = VariantProps<typeof avatarGroupVariants>;
