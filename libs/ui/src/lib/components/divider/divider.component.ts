import { ChangeDetectionStrategy, Component, computed, input, ViewEncapsulation } from '@angular/core';

import type { ClassValue } from 'clsx';

import { mergeClasses } from '../../utils/merge-classes';

import { dividerVariants, type UiDividerVariants } from './divider.variants';

@Component({
  selector: 'ui-divider',
  standalone: true,
  template: '',
  changeDetection: ChangeDetectionStrategy.OnPush,
  encapsulation: ViewEncapsulation.None,
  host: {
    '[attr.role]': `'separator'`,
    '[attr.aria-orientation]': 'uiOrientation()',
    '[class]': 'classes()',
  },
  exportAs: 'uiDivider',
})
export class UiDividerComponent {
  readonly uiOrientation = input<UiDividerVariants['uiOrientation']>('horizontal');
  readonly uiSpacing = input<UiDividerVariants['uiSpacing']>('default');
  readonly class = input<ClassValue>('');

  protected readonly classes = computed(() =>
    mergeClasses(
      dividerVariants({
        uiOrientation: this.uiOrientation(),
        uiSpacing: this.uiSpacing(),
      }),
      this.class(),
    ),
  );
}
