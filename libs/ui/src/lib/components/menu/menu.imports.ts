import { UiContextMenuDirective } from './context-menu.directive';
import { UiMenuContentDirective } from './menu-content.directive';
import { UiMenuItemDirective } from './menu-item.directive';
import { UiMenuLabelComponent } from './menu-label.component';
import { UiMenuShortcutComponent } from './menu-shortcut.component';
import { UiMenuDirective } from './menu.directive';

export const UiMenuImports = [
  UiContextMenuDirective,
  UiMenuContentDirective,
  UiMenuItemDirective,
  UiMenuDirective,
  UiMenuLabelComponent,
  UiMenuShortcutComponent,
] as const;
