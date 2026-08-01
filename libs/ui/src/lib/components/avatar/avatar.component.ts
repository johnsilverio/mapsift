import { NgOptimizedImage } from '@angular/common';
import {
  booleanAttribute,
  ChangeDetectionStrategy,
  Component,
  computed,
  effect,
  input,
  signal,
  ViewEncapsulation,
} from '@angular/core';
import type { SafeUrl } from '@angular/platform-browser';

import { mergeClasses } from '../../utils/merge-classes';

import { avatarVariants, imageVariants, type UiAvatarVariants, type UiImageVariants } from './avatar.variants';

export type UiAvatarStatus = 'online' | 'offline' | 'doNotDisturb' | 'away';

@Component({
  selector: 'ui-avatar, [ui-avatar]',
  imports: [NgOptimizedImage],
  template: `
    @if (uiFallback() && (!uiSrc() || !imageLoaded())) {
      <span class="absolute z-0 m-auto text-base">{{ uiFallback() }}</span>
    }

    @if (uiSrc() && !imageError()) {
      <img
        fill
        sizes="100%"
        [alt]="uiAlt()"
        [class]="imgClasses()"
        [ngSrc]="uiSrc()"
        [priority]="uiPriority()"
        (error)="onImageError()"
        (load)="onImageLoad()"
      />
    }

    @if (uiStatus()) {
      @switch (uiStatus()) {
        @case ('online') {
          <svg
            xmlns="http://www.w3.org/2000/svg"
            width="24"
            height="24"
            viewBox="0 0 24 24"
            fill="currentColor"
            stroke="white"
            stroke-width="2"
            stroke-linecap="round"
            stroke-linejoin="round"
            class="absolute -right-1.25 -bottom-1.25 z-20 h-5 w-5 text-green-500"
          >
            <circle cx="12" cy="12" r="10" fill="currentColor" />
          </svg>
        }
        @case ('offline') {
          <svg
            xmlns="http://www.w3.org/2000/svg"
            width="24"
            height="24"
            viewBox="0 0 24 24"
            fill="currentColor"
            stroke="white"
            stroke-width="2"
            stroke-linecap="round"
            stroke-linejoin="round"
            class="absolute -right-1.25 -bottom-1.25 z-20 h-5 w-5 text-red-500"
          >
            <circle cx="12" cy="12" r="10" fill="currentColor" />
          </svg>
        }
        @case ('doNotDisturb') {
          <svg
            xmlns="http://www.w3.org/2000/svg"
            width="24"
            height="24"
            viewBox="0 0 24 24"
            fill="currentColor"
            stroke="white"
            stroke-width="2"
            stroke-linecap="round"
            stroke-linejoin="round"
            class="absolute -right-1.25 -bottom-1.25 z-20 h-5 w-5 text-red-500"
          >
            <circle cx="12" cy="12" r="10" />
            <path d="M8 12h8" fill="currentColor" />
          </svg>
        }
        @case ('away') {
          <svg
            xmlns="http://www.w3.org/2000/svg"
            width="24"
            height="24"
            viewBox="0 0 24 24"
            fill="currentColor"
            stroke="white"
            stroke-width="2"
            stroke-linecap="round"
            stroke-linejoin="round"
            class="absolute -right-1.25 -bottom-1.25 z-20 h-5 w-5 rotate-y-180 text-yellow-400"
          >
            <path d="M12 3a6 6 0 0 0 9 9 9 9 0 1 1-9-9Z" fill="currentColor" />
          </svg>
        }
      }
    }
  `,
  changeDetection: ChangeDetectionStrategy.OnPush,
  encapsulation: ViewEncapsulation.None,
  host: {
    '[class]': 'containerClasses()',
    '[style.width]': 'customSize()',
    '[style.height]': 'customSize()',
    '[attr.data-slot]': '"avatar"',
    '[attr.data-status]': 'uiStatus() ?? null',
  },
  exportAs: 'uiAvatar',
})
export class UiAvatarComponent {
  readonly class = input<string>('');
  readonly uiAlt = input<string>('');
  readonly uiFallback = input<string>('');
  readonly uiPriority = input(false, { transform: booleanAttribute });
  readonly uiShape = input<UiImageVariants['uiShape']>('circle');
  readonly uiSize = input<UiAvatarVariants['uiSize'] | number>('default');
  readonly uiSrc = input<string | SafeUrl>('');
  readonly uiStatus = input<UiAvatarStatus>();

  protected readonly imageError = signal(false);
  protected readonly imageLoaded = signal(false);

  constructor() {
    effect(() => {
      // Reset image state when uiSrc changes
      this.uiSrc();
      this.imageError.set(false);
      this.imageLoaded.set(false);
    });
  }

  protected readonly containerClasses = computed(() => {
    const size = this.uiSize();
    const uiSize = typeof size === 'number' ? undefined : (size as UiAvatarVariants['uiSize']);

    return mergeClasses(avatarVariants({ uiShape: this.uiShape(), uiSize }), this.class());
  });

  protected readonly customSize = computed(() => {
    const size = this.uiSize();
    return typeof size === 'number' ? `${size}px` : null;
  });

  protected readonly imgClasses = computed(() => mergeClasses(imageVariants({ uiShape: this.uiShape() })));

  protected onImageLoad(): void {
    this.imageLoaded.set(true);
    this.imageError.set(false);
  }

  protected onImageError(): void {
    this.imageError.set(true);
    this.imageLoaded.set(false);
  }
}
