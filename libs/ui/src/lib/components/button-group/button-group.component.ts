import {
  ChangeDetectionStrategy,
  Component,
  computed,
  Directive,
  inject,
  input,
  ViewEncapsulation,
} from '@angular/core';

import { type ClassValue } from 'clsx';

import { mergeClasses } from '../../utils/merge-classes';

import {
  buttonGroupDividerVariants,
  buttonGroupTextVariants,
  buttonGroupVariants,
  type UiButtonGroupVariants,
} from './button-group.variants';
import { UiDividerComponent } from '../divider/divider.component';
import { type UiDividerVariants } from '../divider/divider.variants';

@Component({
  selector: 'ui-button-group',
  template: `
    <ng-content />
  `,
  changeDetection: ChangeDetectionStrategy.OnPush,
  encapsulation: ViewEncapsulation.None,
  host: {
    role: 'group',
    '[class]': 'classes()',
    '[attr.aria-orientation]': 'uiOrientation()',
  },
  exportAs: 'uiButtonGroup',
})
export class UiButtonGroupComponent {
  readonly uiOrientation = input<Required<UiButtonGroupVariants>['uiOrientation']>('horizontal');
  readonly class = input<ClassValue>('');

  protected readonly classes = computed(() =>
    mergeClasses(
      buttonGroupVariants({
        uiOrientation: this.uiOrientation(),
      }),
      this.class(),
    ),
  );
}

@Component({
  selector: 'ui-button-group-divider',
  imports: [UiDividerComponent],
  template: `
    <ui-divider [class]="classes()" uiSpacing="none" aria-hidden="true" [uiOrientation]="orientation()" />
  `,
  changeDetection: ChangeDetectionStrategy.OnPush,
  encapsulation: ViewEncapsulation.None,
  host: {
    class: 'contents',
  },
  exportAs: 'uiButtonGroupDivider',
})
export class UiButtonGroupDividerComponent {
  readonly uiOrientation = input<UiDividerVariants['uiOrientation']>(null);
  readonly class = input<ClassValue>('');

  private readonly parent = inject(UiButtonGroupComponent, {
    optional: true,
    host: true,
  });

  protected readonly orientation = computed(() => {
    if (!this.parent || typeof this.uiOrientation() === 'string') {
      return this.uiOrientation();
    }

    return this.parent.uiOrientation() === 'vertical' ? 'horizontal' : 'vertical';
  });

  protected readonly classes = computed(() =>
    mergeClasses(
      buttonGroupDividerVariants({
        uiOrientation: this.orientation(),
      }),
      this.class(),
    ),
  );
}

@Directive({
  selector: '[ui-button-group-text]',
  host: {
    '[class]': 'classes()',
  },
  exportAs: 'uiButtonGroupText',
})
export class UiButtonGroupTextDirective {
  readonly class = input<ClassValue>('');

  protected readonly classes = computed(() => mergeClasses(buttonGroupTextVariants(), this.class()));
}
