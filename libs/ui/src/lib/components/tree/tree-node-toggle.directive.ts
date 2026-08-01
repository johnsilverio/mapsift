import { computed, Directive, inject, input } from '@angular/core';

import { mergeClasses } from '../../utils/merge-classes';

import { UiTreeService } from './tree.service';
import { treeNodeToggleVariants } from './tree.variants';

@Directive({
  selector: '[ui-tree-node-toggle]',
  host: {
    role: 'button',
    '[class]': 'classes()',
    '[attr.aria-label]': 'isExpanded() ? "Collapse" : "Expand"',
    '[attr.tabindex]': '-1',
    '(click)': 'onClick($event)',
  },
  exportAs: 'uiTreeNodeToggle',
})
export class UiTreeNodeToggleDirective {
  private readonly treeService = inject(UiTreeService);

  readonly nodeKey = input.required<string>({ alias: 'ui-tree-node-toggle' });

  readonly isExpanded = computed(() => this.treeService.isExpanded(this.nodeKey()));

  protected readonly classes = computed(() => mergeClasses(treeNodeToggleVariants({ isExpanded: this.isExpanded() })));

  onClick(event: Event) {
    event.stopPropagation();
    this.treeService.toggle(this.nodeKey());
  }
}
