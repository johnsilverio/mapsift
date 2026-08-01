import { ChangeDetectionStrategy, Component, computed, input, ViewEncapsulation } from '@angular/core';

import { NgIcon, provideIcons } from '@ng-icons/core';
import type { ClassValue } from 'clsx';

import { mergeClasses } from '../../utils/merge-classes';

import { iconVariants, type UiIconSizeVariants } from './icon.variants';
import { UI_ICONS, type UiIcon } from './icons';

/**
 * The one icon primitive every other component in this library renders through. Icons are
 * registered here, so consuming an icon-bearing component obliges the application to provide
 * nothing.
 */
@Component({
  selector: 'ui-icon, [ui-icon]',
  imports: [NgIcon],
  providers: [provideIcons(UI_ICONS)],
  template: `
    <ng-icon [name]="uiType()" [strokeWidth]="uiStrokeWidth()" [class]="classes()" />
  `,
  changeDetection: ChangeDetectionStrategy.OnPush,
  encapsulation: ViewEncapsulation.None,
})
export class UiIconComponent {
  readonly uiType = input.required<UiIcon>();
  readonly uiSize = input<UiIconSizeVariants>('default');
  readonly uiStrokeWidth = input<number>(2);
  readonly class = input<ClassValue>('');

  protected readonly classes = computed(() =>
    mergeClasses(
      iconVariants({ uiSize: this.uiSize() }),
      this.class(),
      this.uiStrokeWidth() === 0 ? 'stroke-none' : '',
    ),
  );
}
