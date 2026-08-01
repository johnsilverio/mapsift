import { DatePipe } from '@angular/common';
import {
  ChangeDetectionStrategy,
  Component,
  computed,
  forwardRef,
  inject,
  input,
  model,
  output,
  viewChild,
  ViewEncapsulation,
  type TemplateRef,
} from '@angular/core';
import { NG_VALUE_ACCESSOR, type ControlValueAccessor } from '@angular/forms';

import type { ClassValue } from 'clsx';

import { UiButtonComponent, type UiButtonTypeVariants } from '../button';
import { UiCalendarComponent } from '../calendar';
import type { UiDatePickerSizeVariants } from './date-picker.variants';
import { UiIconComponent } from '../icon';
import { UiPopoverComponent, UiPopoverDirective } from '../popover';
import { mergeClasses, noopFn } from '../../utils/merge-classes';

/**
 * Height overrides for date-picker sizes.
 *
 * These heights intentionally differ from button size variants to accommodate
 * the date-picker UI:
 * - default: h-9 (vs button h-8)
 * - lg: h-11 (vs button h-9)
 *
 * The `mergeClasses` utility (tailwind-merge) resolves class conflicts,
 * allowing these values to override the base button heights defined in
 * `UiDatePickerSizeVariants`.
 */
const HEIGHT_BY_SIZE: Record<UiDatePickerSizeVariants, string> = {
  xs: 'h-7',
  sm: 'h-8',
  default: 'h-9',
  lg: 'h-11',
};

@Component({
  selector: 'ui-date-picker, [ui-date-picker]',
  imports: [UiButtonComponent, UiCalendarComponent, UiPopoverComponent, UiPopoverDirective, UiIconComponent],
  template: `
    <button
      ui-button
      type="button"
      [uiType]="uiType()"
      [uiSize]="uiSize()"
      [disabled]="disabled()"
      [class]="buttonClasses()"
      uiPopover
      #popoverDirective="uiPopover"
      [uiContent]="calendarTemplate"
      uiTrigger="click"
      (uiVisibleChange)="onPopoverVisibilityChange($event)"
      [attr.aria-expanded]="false"
      [attr.aria-haspopup]="true"
      aria-label="Choose date"
    >
      <ui-icon uiType="calendar" />
      <span [class]="textClasses()">
        {{ displayText() }}
      </span>
    </button>

    <ng-template #calendarTemplate>
      <ui-popover [class]="popoverClasses()">
        <ui-calendar
          #calendar
          class="border-0"
          [value]="value()"
          [minDate]="minDate()"
          [maxDate]="maxDate()"
          [disabled]="disabled()"
          (dateChange)="onDateChange($event)"
        />
      </ui-popover>
    </ng-template>
  `,
  providers: [
    DatePipe,
    {
      provide: NG_VALUE_ACCESSOR,
      useExisting: forwardRef(() => UiDatePickerComponent),
      multi: true,
    },
  ],
  changeDetection: ChangeDetectionStrategy.OnPush,
  encapsulation: ViewEncapsulation.None,
  host: {
    '[class]': 'class()',
  },
  exportAs: 'uiDatePicker',
})
export class UiDatePickerComponent implements ControlValueAccessor {
  private readonly datePipe = inject(DatePipe);

  readonly calendarTemplate = viewChild.required<TemplateRef<unknown>>('calendarTemplate');
  readonly popoverDirective = viewChild.required<UiPopoverDirective>('popoverDirective');
  readonly calendar = viewChild.required<UiCalendarComponent>('calendar');

  readonly class = input<ClassValue>('');
  readonly uiType = input<UiButtonTypeVariants>('outline');
  readonly uiSize = input<UiDatePickerSizeVariants>('default');
  readonly value = model<Date | null>(null);
  readonly placeholder = input<string>('Pick a date');
  readonly uiFormat = input<string>('MMMM d, yyyy');
  readonly minDate = input<Date | null>(null);
  readonly maxDate = input<Date | null>(null);
  readonly disabled = model<boolean>(false);

  readonly dateChange = output<Date | null>();

  private onChange: (value: Date | null) => void = noopFn;
  private onTouched: () => void = noopFn;

  protected readonly buttonClasses = computed(() => {
    const hasValue = !!this.value();
    const size = this.uiSize();
    const height = HEIGHT_BY_SIZE[size];
    return mergeClasses(
      'justify-start text-left font-normal',
      !hasValue && 'text-muted-foreground',
      height,
      'min-w-[240px]',
    );
  });

  protected readonly textClasses = computed(() => {
    const hasValue = !!this.value();
    return mergeClasses(!hasValue && 'text-muted-foreground');
  });

  protected readonly popoverClasses = computed(() => mergeClasses('w-auto p-0'));

  protected readonly displayText = computed(() => {
    const date = this.value();
    if (!date) {
      return this.placeholder();
    }
    return this.formatDate(date, this.uiFormat());
  });

  protected onDateChange(date: Date | Date[]): void {
    // Date picker always uses single mode, so we can safely cast
    const singleDate = Array.isArray(date) ? (date[0] ?? null) : date;
    this.value.set(singleDate);
    this.onChange(singleDate);
    this.onTouched();
    this.dateChange.emit(singleDate);

    this.popoverDirective().hide();
  }

  protected onPopoverVisibilityChange(visible: boolean): void {
    if (visible) {
      setTimeout(() => {
        if (this.calendar()) {
          this.calendar().resetNavigation();
        }
      });
    }
  }

  private formatDate(date: Date, format: string): string {
    return this.datePipe.transform(date, format) ?? '';
  }

  writeValue(value: Date | null): void {
    this.value.set(value);
  }

  registerOnChange(fn: (value: Date | null) => void): void {
    this.onChange = fn;
  }

  registerOnTouched(fn: () => void): void {
    this.onTouched = fn;
  }

  setDisabledState(isDisabled: boolean): void {
    this.disabled.set(isDisabled);
  }
}
