import {
  type AfterContentInit,
  ChangeDetectionStrategy,
  Component,
  computed,
  contentChildren,
  input,
  ViewEncapsulation,
} from '@angular/core';

import type { ClassValue } from 'clsx';

import { UiAccordionItemComponent } from './accordion-item.component';
import { accordionVariants } from './accordion.variants';
import { mergeClasses } from '../../utils/merge-classes';

@Component({
  selector: 'ui-accordion',
  template: `
    <ng-content />
  `,
  changeDetection: ChangeDetectionStrategy.OnPush,
  encapsulation: ViewEncapsulation.None,
  host: {
    '[class]': 'classes()',
  },
  exportAs: 'uiAccordion',
})
export class UiAccordionComponent implements AfterContentInit {
  readonly items = contentChildren(UiAccordionItemComponent);

  readonly class = input<ClassValue>('');
  readonly uiType = input<'single' | 'multiple'>('single');
  readonly uiCollapsible = input<boolean>(true);
  readonly uiDefaultValue = input<string | string[]>('');

  private readonly defaultValue = computed(() => {
    const defaultValue = this.uiDefaultValue();
    if (typeof defaultValue === 'string') {
      return defaultValue ? [defaultValue] : [];
    } else if (this.uiType() === 'single') {
      throw new Error('Array of default values is supported only for multiple uiType');
    }
    return defaultValue;
  });

  protected readonly classes = computed(() => mergeClasses(accordionVariants(), this.class()));

  ngAfterContentInit(): void {
    for (const item of this.items()) {
      item.accordion = this;
      item.isOpen.set(this.defaultValue().includes(item.uiValue()));
    }
  }

  toggleItem(selectedItem: UiAccordionItemComponent): void {
    if (this.uiType() === 'single') {
      this.toggleForSingleType(selectedItem);
    } else {
      this.toggleForMultipleType(selectedItem);
    }
  }

  private toggleForSingleType(selectedItem: UiAccordionItemComponent): void {
    const isClosing = selectedItem.isOpen();

    if (isClosing && !this.uiCollapsible()) {
      return;
    }

    for (const item of this.items()) {
      const shouldBeOpen = item === selectedItem ? !item.isOpen() : false;
      item.isOpen.set(shouldBeOpen);
    }
  }

  private toggleForMultipleType(selectedItem: UiAccordionItemComponent): void {
    const isClosing = selectedItem.isOpen();
    if (isClosing && !this.uiCollapsible() && this.countOpenItems() <= 1) {
      return;
    }

    selectedItem.isOpen.update(v => !v);
  }

  private countOpenItems(): number {
    return this.items().reduce((counter, item) => (item.isOpen() ? ++counter : counter), 0);
  }
}
