import { Injectable } from '@angular/core';

import type { UiMenuDirective } from './menu.directive';

@Injectable({
  providedIn: 'root',
})
export class UiMenuManagerService {
  private activeHoverMenu: UiMenuDirective | null = null;

  registerHoverMenu(menu: UiMenuDirective): void {
    if (this.activeHoverMenu && this.activeHoverMenu !== menu) {
      this.activeHoverMenu.close();
    }
    this.activeHoverMenu = menu;
  }

  unregisterHoverMenu(menu: UiMenuDirective): void {
    if (this.activeHoverMenu === menu) {
      this.activeHoverMenu = null;
    }
  }

  closeActiveMenu(): void {
    if (this.activeHoverMenu) {
      this.activeHoverMenu.close();
      this.activeHoverMenu = null;
    }
  }
}
