import { ChangeDetectionStrategy, Component, ViewEncapsulation, computed, inject, input } from '@angular/core';

import { type ClassValue } from 'clsx';

import { UiCarouselComponent } from './carousel.component';
import { carouselContentVariants } from './carousel.variants';
import { mergeClasses } from '../../utils/merge-classes';

@Component({
  selector: 'ui-carousel-content',
  imports: [],
  template: `
    <ng-content />
  `,
  changeDetection: ChangeDetectionStrategy.OnPush,
  encapsulation: ViewEncapsulation.None,
  host: {
    '[class]': 'classes()',
  },
})
export class UiCarouselContentComponent {
  readonly #parent = inject(UiCarouselComponent);
  readonly #orientation = computed<'horizontal' | 'vertical'>(() => this.#parent.uiOrientation());
  readonly class = input<ClassValue>('');
  protected readonly classes = computed(() =>
    mergeClasses(carouselContentVariants({ uiOrientation: this.#orientation() }), this.class()),
  );
}
