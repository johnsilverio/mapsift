import { Directive, ElementRef, inject, input, type OnInit, ViewContainerRef } from '@angular/core';

import type { UiDropdownMenuContentComponent } from './dropdown-menu-content.component';
import { UiDropdownService } from './dropdown.service';

@Directive({
  selector: '[ui-dropdown], [uiDropdown]',
  host: {
    '[attr.tabindex]': '0',
    '[attr.role]': '"button"',
    '[attr.aria-haspopup]': '"menu"',
    '[attr.aria-expanded]': 'dropdownService.isOpen()',
    '[attr.aria-disabled]': 'uiDisabled()',
    '(click.prevent-with-stop)': 'onClick()',
    '(mouseenter)': 'onHoverToggle($event)',
    '(mouseleave)': 'onHoverToggle($event)',
    '(keydown.{enter,space}.prevent-with-stop)': 'toggleDropdown()',
    '(keydown.arrowdown.prevent)': 'openDropdown()',
  },
  exportAs: 'uiDropdown',
})
export class UiDropdownDirective implements OnInit {
  private readonly elementRef = inject(ElementRef);
  private readonly viewContainerRef = inject(ViewContainerRef);
  protected readonly dropdownService = inject(UiDropdownService);

  readonly uiDropdownMenu = input<UiDropdownMenuContentComponent>();
  readonly uiTrigger = input<'click' | 'hover'>('click');
  readonly uiDisabled = input<boolean>(false);

  ngOnInit() {
    // Ensure button has proper accessibility attributes
    const element = this.elementRef.nativeElement;
    if (!element.hasAttribute('aria-label') && !element.hasAttribute('aria-labelledby')) {
      const label = element.textContent?.trim();
      element.setAttribute('aria-label', label?.length ? label : 'Open menu');
    }
  }

  protected onClick() {
    if (this.uiTrigger() !== 'click') {
      return;
    }

    this.toggleDropdown();
  }

  protected onHoverToggle(event: MouseEvent) {
    if (this.uiTrigger() !== 'hover' || this.uiDisabled()) {
      return;
    }

    if (event.type === 'mouseenter') {
      this.openDropdown();
    } else if (event.type === 'mouseleave') {
      this.closeDropdown();
    }
  }

  protected toggleDropdown() {
    if (this.uiDisabled()) {
      return;
    }

    const menuContent = this.uiDropdownMenu();
    if (menuContent) {
      this.dropdownService.toggle(this.elementRef, menuContent.contentTemplate(), this.viewContainerRef);
    }
  }

  protected openDropdown() {
    if (this.uiDisabled()) {
      return;
    }

    const menuContent = this.uiDropdownMenu();
    if (menuContent && !this.dropdownService.isOpen()) {
      this.dropdownService.toggle(this.elementRef, menuContent.contentTemplate(), this.viewContainerRef);
    }
  }

  protected closeDropdown() {
    this.dropdownService.close();
  }
}
