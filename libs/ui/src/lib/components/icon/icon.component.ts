import { ChangeDetectionStrategy, Component, computed, input, ViewEncapsulation } from '@angular/core';

import { NgIcon, provideIcons } from '@ng-icons/core';
import type { ClassValue } from 'clsx';

import { mergeClasses } from '../../utils/merge-classes';

import { iconVariants, type UiIconSizeVariants } from './icon.variants';
import { UI_ICONS, type UiIcon } from './icons';

/**
 * The one icon primitive. Every other component in this library renders its icons through
 * it, so the set, the sizing scale and the stroke behave identically everywhere.
 *
 * The icon set is registered here rather than by the consuming application, which keeps the
 * library self-contained: importing a component that happens to render a chevron never
 * obliges the application to know that, or to provide anything for it.
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
