import { ChangeDetectionStrategy, Component, ViewEncapsulation, computed, inject, input } from '@angular/core';

import { type ClassValue } from 'clsx';

import { UiCarouselComponent } from './carousel.component';
import { carouselItemVariants } from './carousel.variants';
import { mergeClasses } from '../../utils/merge-classes';

@Component({
  selector: 'ui-carousel-item',
  template: `
    <ng-content />
  `,
  changeDetection: ChangeDetectionStrategy.OnPush,
  encapsulation: ViewEncapsulation.None,
  host: {
    '[class]': 'classes()',
    role: 'group',
    'aria-roledescription': 'slide',
  },
})
export class UiCarouselItemComponent {
  readonly #parent = inject(UiCarouselComponent);

  readonly #orientation = computed<'horizontal' | 'vertical'>(() => this.#parent.uiOrientation());
  readonly class = input<ClassValue>('');
  protected readonly classes = computed(() =>
    mergeClasses(carouselItemVariants({ uiOrientation: this.#orientation() }), this.class()),
  );
}
