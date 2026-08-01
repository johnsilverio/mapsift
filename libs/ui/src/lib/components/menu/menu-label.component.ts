import type { BooleanInput } from '@angular/cdk/coercion';
import {
  booleanAttribute,
  ChangeDetectionStrategy,
  Component,
  computed,
  input,
  ViewEncapsulation,
} from '@angular/core';

import type { ClassValue } from 'clsx';

import { menuLabelVariants } from './menu.variants';
import { mergeClasses } from '../../utils/merge-classes';

@Component({
  selector: 'ui-menu-label, [ui-menu-label]',
  template: `
    <ng-content />
  `,
  changeDetection: ChangeDetectionStrategy.OnPush,
  encapsulation: ViewEncapsulation.None,
  host: {
    '[class]': 'classes()',
    '[attr.data-inset]': 'inset() || null',
  },
  exportAs: 'uiMenuLabel',
})
export class UiMenuLabelComponent {
  readonly class = input<ClassValue>('');
  readonly inset = input<boolean, BooleanInput>(false, { transform: booleanAttribute });

  protected readonly classes = computed(() =>
    mergeClasses(
      menuLabelVariants({
        inset: this.inset(),
      }),
      this.class(),
    ),
  );
}
