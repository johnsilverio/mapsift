import {
  booleanAttribute,
  ChangeDetectionStrategy,
  Component,
  computed,
  forwardRef,
  input,
  output,
  signal,
  ViewEncapsulation,
} from '@angular/core';
import { type ControlValueAccessor, NG_VALUE_ACCESSOR } from '@angular/forms';

import type { ClassValue } from 'clsx';

import { UiIdDirective } from '../../core';
import { mergeClasses, noopFn } from '../../utils/merge-classes';

import {
  checkboxLabelVariants,
  checkboxVariants,
  type UiCheckboxShapeVariants,
  type UiCheckboxSizeVariants,
  type UiCheckboxTypeVariants,
} from './checkbox.variants';
import { UiIconComponent } from '../icon/icon.component';

type OnTouchedType = () => void;
type OnChangeType = (value: boolean) => void;

@Component({
  selector: 'ui-checkbox, [ui-checkbox]',
  imports: [UiIconComponent, UiIdDirective],
  template: `
    <main class="relative flex" uiId="checkbox" #z="uiId">
      <input
        #input
        type="checkbox"
        name="checkbox"
        [id]="z.id()"
        [class]="classes()"
        [checked]="checked()"
        [disabled]="disabled()"
        (blur)="onCheckboxBlur()"
        (click)="onCheckboxChange()"
      />
      <ui-icon
        uiType="check"
        [class]="
          'text-primary-foreground pointer-events-none absolute top-1/2 left-1/2 flex -translate-x-1/2 -translate-y-1/2 items-center justify-center transition-opacity ' +
          (checked() ? 'opacity-100' : 'opacity-0')
        "
      />
    </main>
    <label [class]="labelClasses()" [for]="z.id()">
      <ng-content />
    </label>
  `,
  providers: [
    {
      provide: NG_VALUE_ACCESSOR,
      useExisting: forwardRef(() => UiCheckboxComponent),
      multi: true,
    },
  ],
  changeDetection: ChangeDetectionStrategy.OnPush,
  encapsulation: ViewEncapsulation.None,
  host: {
    '[class]': "(disabled() ? 'cursor-not-allowed' : 'cursor-pointer') + ' flex items-center gap-2'",
    '[attr.aria-disabled]': 'disabled()',
  },
  exportAs: 'uiCheckbox',
})
export class UiCheckboxComponent implements ControlValueAccessor {
  readonly checkChange = output<boolean>();

  readonly class = input<ClassValue>('');
  readonly uiDisabled = input(false, { transform: booleanAttribute });
  readonly uiType = input<UiCheckboxTypeVariants>('default');
  readonly uiSize = input<UiCheckboxSizeVariants>('default');
  readonly uiShape = input<UiCheckboxShapeVariants>('default');

  private onChange: OnChangeType = noopFn;
  private onTouched: OnTouchedType = noopFn;

  protected readonly classes = computed(() =>
    mergeClasses(checkboxVariants({ uiType: this.uiType(), uiSize: this.uiSize(), uiShape: this.uiShape() }), this.class()),
  );

  readonly disabledByForm = signal(false);
  protected readonly labelClasses = computed(() => mergeClasses(checkboxLabelVariants({ uiSize: this.uiSize() })));
  protected readonly disabled = computed(() => this.uiDisabled() || this.disabledByForm());
  readonly checked = signal(false);

  writeValue(val: boolean): void {
    this.checked.set(val);
  }

  setDisabledState(isDisabled: boolean): void {
    this.disabledByForm.set(isDisabled);
  }

  registerOnChange(fn: OnChangeType): void {
    this.onChange = fn;
  }

  registerOnTouched(fn: OnTouchedType): void {
    this.onTouched = fn;
  }

  onCheckboxBlur(): void {
    this.onTouched();
  }

  onCheckboxChange(): void {
    if (this.disabled()) {
      return;
    }

    this.checked.update(v => !v);
    this.onChange(this.checked());
    this.checkChange.emit(this.checked());
  }
}
