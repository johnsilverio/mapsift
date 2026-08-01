import { ChangeDetectionStrategy, Component, computed, input, signal, ViewEncapsulation } from '@angular/core';

import type { ClassValue } from 'clsx';

import type { UiAccordionComponent } from './accordion.component';
import {
  accordionContentVariants,
  accordionItemVariants,
  accordionTriggerVariants,
} from './accordion.variants';
import { UiIconComponent } from '../icon';
import { mergeClasses } from '../../utils/merge-classes';

@Component({
  selector: 'ui-accordion-item',
  imports: [UiIconComponent],
  template: `
    <button
      type="button"
      [attr.aria-controls]="'content-' + uiValue()"
      [attr.aria-expanded]="isOpen()"
      [id]="'accordion-' + uiValue()"
      [class]="triggerClasses()"
      (click)="toggle()"
    >
      {{ uiTitle() }}
      <ui-icon
        uiType="chevron-down"
        class="text-muted-foreground pointer-events-none size-4 shrink-0 translate-y-0.5 transition-transform duration-200"
        [class]="isOpen() ? 'rotate-180' : ''"
      />
    </button>

    <div
      role="region"
      [attr.aria-labelledby]="'accordion-' + uiValue()"
      [attr.data-state]="isOpen() ? 'open' : 'closed'"
      [id]="'content-' + uiValue()"
      [class]="contentClasses()"
    >
      <div class="overflow-hidden">
        <div class="pt-0 pb-4">
          <ng-content />
        </div>
      </div>
    </div>
  `,
  changeDetection: ChangeDetectionStrategy.OnPush,
  encapsulation: ViewEncapsulation.None,
  host: {
    '[class]': 'itemClasses()',
    '[attr.data-state]': "isOpen() ? 'open' : 'closed'",
  },
  exportAs: 'uiAccordionItem',
})
export class UiAccordionItemComponent {
  readonly uiTitle = input<string>('');
  readonly uiValue = input<string>('');
  readonly class = input<ClassValue>('');

  accordion!: UiAccordionComponent;
  readonly isOpen = signal(false);

  protected readonly itemClasses = computed(() => mergeClasses(accordionItemVariants(), this.class()));
  protected readonly triggerClasses = computed(() => mergeClasses(accordionTriggerVariants()));
  protected readonly contentClasses = computed(() => mergeClasses(accordionContentVariants({ isOpen: this.isOpen() })));

  toggle(): void {
    if (this.accordion) {
      this.accordion.toggleItem(this);
    } else {
      this.isOpen.update(v => !v);
    }
  }
}
