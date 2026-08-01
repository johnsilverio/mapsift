import { ChangeDetectionStrategy, Component, computed, input, ViewEncapsulation } from '@angular/core';

import type { ClassValue } from 'clsx';

import { mergeClasses } from '../../utils/merge-classes';

import { avatarGroupVariants, type UiAvatarGroupVariants } from './avatar.variants';

@Component({
  selector: 'ui-avatar-group',
  template: `
    <ng-content />
  `,
  changeDetection: ChangeDetectionStrategy.OnPush,
  encapsulation: ViewEncapsulation.None,
  host: {
    '[class]': 'classes()',
  },
  exportAs: 'uiAvatarGroup',
})
export class UiAvatarGroupComponent {
  readonly uiOrientation = input<UiAvatarGroupVariants['uiOrientation']>('horizontal');
  readonly class = input<ClassValue>('');

  protected readonly classes = computed(() =>
    mergeClasses(avatarGroupVariants({ uiOrientation: this.uiOrientation() }), this.class()),
  );
}
