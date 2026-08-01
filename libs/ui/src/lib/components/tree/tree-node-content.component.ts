import { ChangeDetectionStrategy, Component, computed, inject, input, ViewEncapsulation } from '@angular/core';

import type { ClassValue } from 'clsx';

import { mergeClasses } from '../../utils/merge-classes';

import { UiTreeService } from './tree.service';
import { treeNodeContentVariants } from './tree.variants';

@Component({
  selector: 'ui-tree-node-content',
  template: `
    <ng-content />
  `,
  changeDetection: ChangeDetectionStrategy.OnPush,
  encapsulation: ViewEncapsulation.None,
  host: {
    '[class]': 'classes()',
  },
  exportAs: 'uiTreeNodeContent',
})
export class UiTreeNodeContentComponent {
  private readonly treeService = inject(UiTreeService);

  readonly class = input<ClassValue>('');
  readonly nodeKey = input.required<string>();

  readonly isSelected = computed(() => this.treeService.isSelected(this.nodeKey()));

  protected readonly classes = computed(() =>
    mergeClasses(treeNodeContentVariants({ isSelected: this.isSelected() }), this.class()),
  );
}
