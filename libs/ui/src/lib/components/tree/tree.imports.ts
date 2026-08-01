import { UiTreeNodeContentComponent } from './tree-node-content.component';
import { UiTreeNodeToggleDirective } from './tree-node-toggle.directive';
import { UiTreeNodeComponent } from './tree-node.component';
import { UiTreeComponent } from './tree.component';

export const UiTreeImports = [
  UiTreeComponent,
  UiTreeNodeComponent,
  UiTreeNodeToggleDirective,
  UiTreeNodeContentComponent,
] as const;
