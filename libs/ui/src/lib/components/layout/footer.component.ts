import { ChangeDetectionStrategy, Component, computed, input, ViewEncapsulation } from '@angular/core';

import type { ClassValue } from 'clsx';

import { footerVariants } from './layout.variants';
import { mergeClasses } from '../../utils/merge-classes';

@Component({
  selector: 'ui-footer',
  template: `
    <footer [class]="classes()" [style.height.px]="uiHeight()">
      <ng-content />
    </footer>
  `,
  changeDetection: ChangeDetectionStrategy.OnPush,
  encapsulation: ViewEncapsulation.None,
  exportAs: 'uiFooter',
})
export class FooterComponent {
  readonly class = input<ClassValue>('');
  readonly uiHeight = input<number>(64);

  protected readonly classes = computed(() => mergeClasses(footerVariants(), this.class()));
}
