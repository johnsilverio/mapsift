import { ChangeDetectionStrategy, Component, computed, input, ViewEncapsulation } from '@angular/core';

import type { ClassValue } from 'clsx';

import { mergeClasses } from '../../utils/merge-classes';

import { badgeVariants, type UiBadgeShapeVariants, type UiBadgeTypeVariants } from './badge.variants';

@Component({
  selector: 'ui-badge',
  template: `
    <ng-content />
  `,
  changeDetection: ChangeDetectionStrategy.OnPush,
  encapsulation: ViewEncapsulation.None,
  host: {
    '[class]': 'classes()',
  },
  exportAs: 'uiBadge',
})
export class UiBadgeComponent {
  readonly uiType = input<UiBadgeTypeVariants>('default');
  readonly uiShape = input<UiBadgeShapeVariants>('default');

  readonly class = input<ClassValue>('');

  protected readonly classes = computed(() =>
    mergeClasses(badgeVariants({ uiType: this.uiType(), uiShape: this.uiShape() }), this.class()),
  );
}
