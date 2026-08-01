import { ChangeDetectionStrategy, Component, computed, contentChildren, input, ViewEncapsulation } from '@angular/core';

import type { ClassValue } from 'clsx';

import { layoutVariants, type LayoutVariants } from './layout.variants';
import { SidebarComponent } from './sidebar.component';
import { mergeClasses } from '../../utils/merge-classes';

@Component({
  selector: 'ui-layout',
  template: `
    <ng-content />
  `,
  changeDetection: ChangeDetectionStrategy.OnPush,
  encapsulation: ViewEncapsulation.None,
  host: {
    '[class]': 'classes()',
  },
  exportAs: 'uiLayout',
})
export class LayoutComponent {
  readonly class = input<ClassValue>('');
  readonly uiDirection = input<LayoutVariants>('auto');

  // Query for direct sidebar children to auto-detect layout direction
  private readonly sidebars = contentChildren(SidebarComponent, { descendants: false });

  private readonly detectedDirection = computed(() => {
    if (this.uiDirection() !== 'auto') {
      return this.uiDirection();
    }

    // Auto-detection: Check if there are any sidebar children
    const hasSidebar = this.sidebars().length > 0;
    return hasSidebar ? 'horizontal' : 'vertical';
  });

  protected readonly classes = computed(() =>
    mergeClasses(
      layoutVariants({
        uiDirection: this.detectedDirection(),
      }),
      this.class(),
    ),
  );
}
