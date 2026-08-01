import { ChangeDetectionStrategy, Component, computed, input, ViewEncapsulation } from '@angular/core';

import type { ClassValue } from 'clsx';
import { LucideAngularModule } from 'lucide-angular';

import { mergeClasses } from '../../utils/merge-classes';

import { iconVariants, type UiIconSizeVariants } from './icon.variants';
import { UI_ICONS, type UiIcon } from './icons';

@Component({
  selector: 'ui-icon, [ui-icon]',
  imports: [LucideAngularModule],
  template: `
    <lucide-angular
      [img]="icon()"
      [strokeWidth]="uiStrokeWidth()"
      [absoluteStrokeWidth]="uiAbsoluteStrokeWidth()"
      [class]="classes()"
    />
  `,
  changeDetection: ChangeDetectionStrategy.OnPush,
  encapsulation: ViewEncapsulation.None,
})
export class UiIconComponent {
  readonly uiType = input.required<UiIcon>();
  readonly uiSize = input<UiIconSizeVariants>('default');
  readonly uiStrokeWidth = input<number>(2);
  readonly uiAbsoluteStrokeWidth = input<boolean>(false);
  readonly class = input<ClassValue>('');

  protected readonly classes = computed(() =>
    mergeClasses(iconVariants({ uiSize: this.uiSize() }), this.class(), this.uiStrokeWidth() === 0 ? 'stroke-none' : ''),
  );

  protected readonly icon = computed(() => {
    const type = this.uiType();
    if (typeof type === 'string') {
      return UI_ICONS[type];
    }

    return type;
  });
}
