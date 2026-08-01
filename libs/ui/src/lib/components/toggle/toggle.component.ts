import {
  booleanAttribute,
  ChangeDetectionStrategy,
  Component,
  computed,
  forwardRef,
  input,
  linkedSignal,
  output,
  signal,
  ViewEncapsulation,
} from '@angular/core';
import { type ControlValueAccessor, NG_VALUE_ACCESSOR } from '@angular/forms';

import type { ClassValue } from 'clsx';

import { mergeClasses } from '../../utils/merge-classes';

import { toggleVariants, type UiToggleVariants } from './toggle.variants';

type OnTouchedType = () => void;
type OnChangeType = (value: boolean) => void;

@Component({
  selector: 'ui-toggle',
  template: `
    <button
      type="button"
      [attr.aria-label]="uiAriaLabel()"
      [attr.aria-pressed]="value()"
      [attr.data-state]="value() ? 'on' : 'off'"
      [class]="classes()"
      [disabled]="disabled()"
      (click)="toggle()"
    >
      <ng-content />
    </button>
  `,
  providers: [
    {
      provide: NG_VALUE_ACCESSOR,
      useExisting: forwardRef(() => UiToggleComponent),
      multi: true,
    },
  ],
  changeDetection: ChangeDetectionStrategy.OnPush,
  encapsulation: ViewEncapsulation.None,
  host: {
    '(mouseenter)': 'handleHover()',
  },
  exportAs: 'uiToggle',
})
export class UiToggleComponent implements ControlValueAccessor {
  readonly uiValue = input<boolean | undefined>();
  readonly uiDefault = input<boolean>(false);
  readonly uiDisabled = input(false, { alias: 'disabled', transform: booleanAttribute });
  readonly uiType = input<UiToggleVariants['uiType']>('default');
  readonly uiSize = input<UiToggleVariants['uiSize']>('md');
  readonly uiAriaLabel = input<string>('', { alias: 'aria-label' });
  readonly class = input<ClassValue>('');

  readonly uiToggleClick = output<void>();
  readonly uiToggleHover = output<void>();
  readonly uiToggleChange = output<boolean>();

  private readonly isUsingNgModel = signal(false);

  protected readonly value = linkedSignal(() => this.uiValue() ?? this.uiDefault());

  protected readonly disabled = linkedSignal(() => this.uiDisabled());

  protected readonly classes = computed(() =>
    mergeClasses(toggleVariants({ uiSize: this.uiSize(), uiType: this.uiType() }), this.class()),
  );

  // eslint-disable-next-line @typescript-eslint/no-empty-function
  private onTouched: OnTouchedType = () => {};
  // eslint-disable-next-line @typescript-eslint/no-empty-function
  private onChangeFn: OnChangeType = () => {};

  handleHover() {
    this.uiToggleHover.emit();
  }

  toggle() {
    if (this.disabled()) {
      return;
    }

    const next = !this.value();

    if (this.uiValue() === undefined) {
      this.value.set(next);
    }

    this.uiToggleClick.emit();
    this.uiToggleChange.emit(next);
    this.onChangeFn(next);
    this.onTouched();
  }

  writeValue(val: boolean): void {
    this.value.set(val ?? this.uiDefault());
  }

  registerOnChange(fn: any): void {
    this.onChangeFn = fn;
    this.isUsingNgModel.set(true);
  }

  registerOnTouched(fn: any): void {
    this.onTouched = fn;
  }

  setDisabledState(isDisabled: boolean): void {
    this.disabled.set(isDisabled);
  }
}
