import {
  booleanAttribute,
  ChangeDetectionStrategy,
  Component,
  computed,
  ElementRef,
  inject,
  input,
  linkedSignal,
  signal,
} from '@angular/core';

import { UiIconComponent } from '../icon';
import {
  selectItemIconVariants,
  selectItemVariants,
  type UiSelectItemModeVariants,
  type UiSelectSizeVariants,
} from './select.variants';
import { mergeClasses, noopFn } from '../../utils/merge-classes';

// Interface to avoid circular dependency
interface SelectHost {
  selectedValue(): string[];
  selectItem(value: string, label: string): void;
  navigateTo(): void;
}

@Component({
  selector: 'ui-select-item, [ui-select-item]',
  imports: [UiIconComponent],
  template: `
    @if (isSelected()) {
      <span [class]="iconClasses()">
        <ui-icon uiType="check" [uiStrokeWidth]="strokeWidth()" aria-hidden="true" data-testid="check-icon" />
      </span>
    }
    <span class="truncate">
      <ng-content />
    </span>
  `,
  changeDetection: ChangeDetectionStrategy.OnPush,
  host: {
    role: 'option',
    tabindex: '-1',
    '[class]': 'classes()',
    '[attr.value]': 'uiValue()',
    '[attr.data-disabled]': 'uiDisabled() ? "" : null',
    '[attr.data-selected]': 'isSelected() ? "" : null',
    '[attr.aria-selected]': 'isSelected()',
    '(click)': 'onClick()',
    '(mouseenter)': 'onMouseEnter()',
    '(keydown.{tab}.prevent)': 'noopFn',
  },
})
export class UiSelectItemComponent {
  readonly elementRef = inject(ElementRef<HTMLElement>);

  readonly uiValue = input.required<string>();
  readonly uiDisabled = input(false, { transform: booleanAttribute });
  readonly class = input<string>('');

  private readonly select = signal<SelectHost | null>(null);
  noopFn = noopFn;

  readonly label = linkedSignal<string>(() => {
    const element = this.elementRef.nativeElement;
    return (element.textContent ?? element.innerText)?.trim() ?? '';
  });

  readonly uiMode = signal<UiSelectItemModeVariants>('normal');
  readonly uiSize = signal<UiSelectSizeVariants>('default');

  protected readonly classes = computed(() =>
    mergeClasses(selectItemVariants({ uiMode: this.uiMode(), uiSize: this.uiSize() }), this.class()),
  );

  protected readonly iconClasses = computed(() =>
    mergeClasses(selectItemIconVariants({ uiMode: this.uiMode(), uiSize: this.uiSize() })),
  );

  protected readonly strokeWidth = computed(() => (this.uiMode() === 'compact' ? 3 : 2));

  protected readonly isSelected = computed(() => this.select()?.selectedValue().includes(this.uiValue()) ?? false);

  setSelectHost(selectHost: SelectHost) {
    this.select.set(selectHost);
  }

  onMouseEnter() {
    if (this.uiDisabled()) {
      return;
    }
    this.select()?.navigateTo();
  }

  onClick() {
    if (this.uiDisabled()) {
      return;
    }
    this.select()?.selectItem(this.uiValue(), this.label());
  }
}
