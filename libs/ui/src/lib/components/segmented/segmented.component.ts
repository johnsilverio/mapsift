import {
  ChangeDetectionStrategy,
  Component,
  computed,
  contentChildren,
  effect,
  forwardRef,
  input,
  type OnInit,
  output,
  signal,
  ViewEncapsulation,
} from '@angular/core';
import { type ControlValueAccessor, NG_VALUE_ACCESSOR } from '@angular/forms';

import type { ClassValue } from 'clsx';

import { mergeClasses } from '../../utils/merge-classes';

import { segmentedItemVariants, segmentedVariants, type UiSegmentedVariants } from './segmented.variants';

export interface SegmentedOption {
  value: string;
  label: string;
  disabled?: boolean;
}
@Component({
  selector: 'ui-segmented-item',
  standalone: true,
  template: `
    <ng-content />
  `,
  encapsulation: ViewEncapsulation.None,
})
export class UiSegmentedItemComponent {
  readonly value = input.required<string>();
  readonly label = input.required<string>();
  readonly disabled = input(false);
}

@Component({
  selector: 'ui-segmented',
  standalone: true,
  template: `
    <div [class]="classes()" role="tablist" [attr.aria-label]="uiAriaLabel()">
      @for (option of uiOptions(); track option.value) {
        <button
          type="button"
          role="tab"
          [class]="getItemClasses(option.value)"
          [disabled]="option.disabled || uiDisabled()"
          [attr.aria-selected]="isSelected(option.value)"
          [attr.aria-controls]="option.value + '-panel'"
          [attr.id]="option.value + '-tab'"
          (click)="selectOption(option.value)"
        >
          {{ option.label }}
        </button>
      } @empty {
        @for (item of items(); track item.value()) {
          <button
            type="button"
            role="tab"
            [class]="getItemClasses(item.value())"
            [disabled]="item.disabled() || uiDisabled()"
            [attr.aria-selected]="isSelected(item.value())"
            [attr.aria-controls]="item.value() + '-panel'"
            [attr.id]="item.value() + '-tab'"
            (click)="selectOption(item.value())"
          >
            {{ item.label() }}
          </button>
        }
      }
    </div>
  `,
  providers: [
    {
      provide: NG_VALUE_ACCESSOR,
      useExisting: forwardRef(() => UiSegmentedComponent),
      multi: true,
    },
  ],
  changeDetection: ChangeDetectionStrategy.OnPush,
  encapsulation: ViewEncapsulation.None,
  host: {
    '[class]': 'wrapperClasses()',
  },
  exportAs: 'uiSegmented',
})
export class UiSegmentedComponent implements ControlValueAccessor, OnInit {
  private readonly itemComponents = contentChildren(UiSegmentedItemComponent);

  readonly class = input<ClassValue>('');
  readonly uiSize = input<UiSegmentedVariants['uiSize']>('default');
  readonly uiOptions = input<SegmentedOption[]>([]);
  readonly uiDefaultValue = input<string>('');
  readonly uiDisabled = input(false);
  readonly uiAriaLabel = input<string>('Segmented control');

  readonly uiChange = output<string>();

  protected readonly selectedValue = signal<string>('');
  protected readonly items = signal<readonly UiSegmentedItemComponent[]>([]);

  // eslint-disable-next-line @typescript-eslint/no-empty-function
  private onChange: (value: string) => void = () => {};
  // eslint-disable-next-line @typescript-eslint/no-empty-function
  private onTouched = () => {};

  constructor() {
    effect(() => {
      this.items.set(this.itemComponents());
    });
  }

  ngOnInit() {
    // Initialize with default value
    if (this.uiDefaultValue()) {
      this.selectedValue.set(this.uiDefaultValue());
    }
  }

  protected readonly classes = computed(() => mergeClasses(segmentedVariants({ uiSize: this.uiSize() }), this.class()));

  protected readonly wrapperClasses = computed(() => 'inline-block');

  protected getItemClasses(value: string): string {
    return segmentedItemVariants({
      uiSize: this.uiSize(),
      isActive: this.isSelected(value),
    });
  }

  protected isSelected(value: string): boolean {
    return this.selectedValue() === value;
  }

  protected selectOption(value: string) {
    if (this.uiDisabled()) {
      return;
    }

    const option = this.uiOptions().find(opt => opt.value === value);
    const item = this.items().find(item => item.value() === value);

    if (option?.disabled || item?.disabled()) {
      return;
    }

    this.selectedValue.set(value);
    this.onChange(value);
    this.onTouched();
    this.uiChange.emit(value);
  }

  // ControlValueAccessor implementation
  writeValue(value: string): void {
    this.selectedValue.set(value ?? '');
  }

  registerOnChange(fn: (value: string) => void): void {
    this.onChange = fn;
  }

  registerOnTouched(fn: () => void): void {
    this.onTouched = fn;
  }

  setDisabledState(_isDisabled: boolean): void {
    // Handled by uiDisabled input
  }
}
