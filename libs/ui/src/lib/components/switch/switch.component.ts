import {
  booleanAttribute,
  ChangeDetectionStrategy,
  Component,
  computed,
  forwardRef,
  input,
  model,
  signal,
  ViewEncapsulation,
} from '@angular/core';
import { type ControlValueAccessor, NG_VALUE_ACCESSOR } from '@angular/forms';

import type { ClassValue } from 'clsx';

import { UiIdDirective } from '../../core';
import { mergeClasses, noopFn } from '../../utils/merge-classes';

import { switchVariants, type UiSwitchSizeVariants, type UiSwitchTypeVariants } from './switch.variants';

type OnTouchedType = () => void;
type OnChangeType = (value: boolean) => void;

@Component({
  selector: 'ui-switch',
  imports: [UiIdDirective],
  template: `
    <span class="flex items-center space-x-2" uiId="switch" #z="uiId">
      <button
        [id]="uiId() || z.id()"
        type="button"
        role="switch"
        [attr.data-state]="status()"
        [attr.aria-checked]="uiChecked()"
        [class]="classes()"
        [disabled]="uiDisabled() || formDisabled()"
        (click)="onSwitchChange()"
      >
        <span
          [attr.data-size]="uiSize()"
          [attr.data-state]="status()"
          class="bg-background pointer-events-none block h-5 w-5 rounded-full shadow-lg ring-0 transition-transform data-[size=lg]:h-6 data-[size=lg]:w-6 data-[size=sm]:h-4 data-[size=sm]:w-4 data-[state=checked]:translate-x-5 data-[size=lg]:data-[state=checked]:translate-x-6 data-[size=sm]:data-[state=checked]:translate-x-4 data-[state=unchecked]:translate-x-0 data-[size=lg]:data-[state=unchecked]:translate-x-0 data-[size=sm]:data-[state=unchecked]:translate-x-0"
        ></span>
      </button>

      <label
        class="text-sm leading-none font-medium peer-disabled:cursor-not-allowed peer-disabled:opacity-70"
        [for]="uiId() || z.id()"
      >
        <ng-content><span class="sr-only">toggle switch</span></ng-content>
      </label>
    </span>
  `,
  providers: [
    {
      provide: NG_VALUE_ACCESSOR,
      useExisting: forwardRef(() => UiSwitchComponent),
      multi: true,
    },
  ],
  changeDetection: ChangeDetectionStrategy.OnPush,
  encapsulation: ViewEncapsulation.None,
  exportAs: 'uiSwitch',
})
export class UiSwitchComponent implements ControlValueAccessor {
  readonly class = input<ClassValue>('');
  readonly uiChecked = model<boolean>(true);
  readonly uiId = input<string>('');
  readonly uiSize = input<UiSwitchSizeVariants>('default');
  readonly uiType = input<UiSwitchTypeVariants>('default');
  readonly uiDisabled = input(false, { transform: booleanAttribute });

  private onChange: OnChangeType = noopFn;
  private onTouched: OnTouchedType = noopFn;

  protected readonly status = computed(() => (this.uiChecked() ? 'checked' : 'unchecked'));
  protected readonly classes = computed(() =>
    mergeClasses(switchVariants({ uiType: this.uiType(), uiSize: this.uiSize() }), this.class()),
  );

  protected readonly formDisabled = signal(false);

  writeValue(val: boolean): void {
    this.uiChecked.set(val);
  }

  registerOnChange(fn: OnChangeType): void {
    this.onChange = fn;
  }

  registerOnTouched(fn: OnTouchedType): void {
    this.onTouched = fn;
  }

  onSwitchChange(): void {
    if (this.uiDisabled() || this.formDisabled()) {
      return;
    }

    this.uiChecked.update(checked => !checked);
    this.onTouched();
    this.onChange(this.uiChecked());
  }

  setDisabledState(isDisabled: boolean): void {
    this.formDisabled.set(isDisabled);
  }
}
