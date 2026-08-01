import {
  booleanAttribute,
  computed,
  Directive,
  effect,
  ElementRef,
  forwardRef,
  inject,
  input,
  linkedSignal,
  model,
} from '@angular/core';
import { NG_VALUE_ACCESSOR, type ControlValueAccessor } from '@angular/forms';

import type { ClassValue } from 'clsx';

import { mergeClasses, noopFn } from '../../utils/merge-classes';

import {
  inputVariants,
  type UiInputSizeVariants,
  type UiInputStatusVariants,
  type UiInputTypeVariants,
} from './input.variants';

type OnTouchedType = () => void;
type OnChangeType = (value: string) => void;

@Directive({
  selector: 'input[ui-input], textarea[ui-input]',
  providers: [
    {
      provide: NG_VALUE_ACCESSOR,
      useExisting: forwardRef(() => UiInputDirective),
      multi: true,
    },
  ],
  host: {
    '[class]': 'classes()',
    '(input)': 'updateValue($event.target)',
    '(blur)': 'onBlur()',
  },
  exportAs: 'uiInput',
})
export class UiInputDirective implements ControlValueAccessor {
  private readonly elementRef = inject(ElementRef);
  private onTouched: OnTouchedType = noopFn;
  private onChangeFn: OnChangeType = noopFn;

  readonly class = input<ClassValue>('');
  readonly uiBorderless = input(false, { transform: booleanAttribute });
  readonly uiSize = input<UiInputSizeVariants>('default');
  readonly uiStatus = input<UiInputStatusVariants>();
  readonly value = model<string>('');

  readonly size = linkedSignal<UiInputSizeVariants>(() => this.uiSize());

  protected readonly classes = computed(() =>
    mergeClasses(
      inputVariants({
        uiType: this.getType(),
        uiSize: this.size(),
        uiStatus: this.uiStatus(),
        uiBorderless: this.uiBorderless(),
      }),
      this.class(),
    ),
  );

  constructor() {
    effect(() => {
      const value = this.value();

      if (value !== undefined && value !== null) {
        this.elementRef.nativeElement.value = value;
      }
    });
  }

  disable(b: boolean): void {
    this.elementRef.nativeElement.disabled = b;
  }

  setDataSlot(name: string): void {
    if (this.elementRef?.nativeElement?.dataset) {
      this.elementRef.nativeElement.dataset.slot = name;
    }
  }

  protected updateValue(target: EventTarget | null): void {
    const el = target as HTMLInputElement | HTMLTextAreaElement | null;
    this.value.set(el?.value ?? '');
    this.onChangeFn(this.value());
  }

  protected onBlur() {
    this.onTouched();
  }

  getType(): UiInputTypeVariants {
    const isTextarea = this.elementRef.nativeElement.tagName.toLowerCase() === 'textarea';
    return isTextarea ? 'textarea' : 'default';
  }

  registerOnChange(fn: OnChangeType): void {
    this.onChangeFn = fn;
  }

  registerOnTouched(fn: OnTouchedType): void {
    this.onTouched = fn;
  }

  setDisabledState(isDisabled: boolean): void {
    this.disable(isDisabled);
  }

  writeValue(value?: string): void {
    const newValue = value ?? '';
    this.value.set(newValue);
    this.elementRef.nativeElement.value = newValue;
  }
}
