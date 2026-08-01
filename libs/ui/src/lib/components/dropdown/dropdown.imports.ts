import { UiDropdownMenuItemComponent } from './dropdown-item.component';
import { UiDropdownMenuContentComponent } from './dropdown-menu-content.component';
import { UiDropdownDirective } from './dropdown-trigger.directive';
import { UiDropdownMenuComponent } from './dropdown.component';
import { UiMenuLabelComponent } from '../menu/menu-label.component';

export const UiDropdownImports = [
  UiDropdownMenuComponent,
  UiDropdownMenuItemComponent,
  UiMenuLabelComponent,
  UiDropdownMenuContentComponent,
  UiDropdownDirective,
] as const;
