import {
  booleanAttribute,
  ChangeDetectionStrategy,
  Component,
  computed,
  input,
  ViewEncapsulation,
} from '@angular/core';

import type { ClassValue } from 'clsx';

import {
  formControlVariants,
  formFieldVariants,
  formLabelVariants,
  formMessageVariants,
  type UiFormMessageTypeVariants,
} from './form.variants';
import { mergeClasses } from '../../utils/merge-classes';

@Component({
  selector: 'ui-form-field, [ui-form-field]',
  template: '<ng-content />',
  changeDetection: ChangeDetectionStrategy.OnPush,
  encapsulation: ViewEncapsulation.None,
  host: {
    '[class]': 'classes()',
  },
  exportAs: 'uiFormField',
})
export class UiFormFieldComponent {
  readonly class = input<ClassValue>('');

  protected readonly classes = computed(() => mergeClasses(formFieldVariants(), this.class()));
}

@Component({
  selector: 'ui-form-control, [ui-form-control]',
  imports: [],
  template: `
    <div class="relative">
      <ng-content />
    </div>
    @if (errorMessage() || helpText()) {
      <div class="mt-1.5 min-h-5">
        @if (errorMessage()) {
          <p class="text-sm text-red-500">{{ errorMessage() }}</p>
        } @else if (helpText()) {
          <p class="text-muted-foreground text-sm">{{ helpText() }}</p>
        }
      </div>
    }
  `,
  changeDetection: ChangeDetectionStrategy.OnPush,
  encapsulation: ViewEncapsulation.None,
  host: {
    '[class]': 'classes()',
  },
  exportAs: 'uiFormControl',
})
export class UiFormControlComponent {
  readonly class = input<ClassValue>('');
  readonly errorMessage = input<string>('');
  readonly helpText = input<string>('');

  protected readonly classes = computed(() => mergeClasses(formControlVariants(), this.class()));
}

@Component({
  selector: 'ui-form-label, label[ui-form-label]',
  template: '<ng-content />',
  changeDetection: ChangeDetectionStrategy.OnPush,
  encapsulation: ViewEncapsulation.None,
  host: {
    '[class]': 'classes()',
  },
  exportAs: 'uiFormLabel',
})
export class UiFormLabelComponent {
  readonly class = input<ClassValue>('');
  readonly uiRequired = input(false, { transform: booleanAttribute });

  protected readonly classes = computed(() =>
    mergeClasses(formLabelVariants({ uiRequired: this.uiRequired() }), this.class()),
  );
}

@Component({
  selector: 'ui-form-message, [ui-form-message]',
  template: '<ng-content />',
  changeDetection: ChangeDetectionStrategy.OnPush,
  encapsulation: ViewEncapsulation.None,
  host: {
    '[class]': 'classes()',
  },
  exportAs: 'uiFormMessage',
})
export class UiFormMessageComponent {
  readonly class = input<ClassValue>('');
  readonly uiType = input<UiFormMessageTypeVariants>('default');

  protected readonly classes = computed(() => mergeClasses(formMessageVariants({ uiType: this.uiType() }), this.class()));
}
