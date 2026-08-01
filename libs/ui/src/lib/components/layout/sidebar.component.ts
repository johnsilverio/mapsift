import {
  booleanAttribute,
  ChangeDetectionStrategy,
  Component,
  computed,
  effect,
  input,
  output,
  signal,
  ViewEncapsulation,
  type TemplateRef,
} from '@angular/core';

import type { ClassValue } from 'clsx';

import { UiIconComponent, type UiIcon } from '../icon';
import {
  sidebarGroupLabelVariants,
  sidebarGroupVariants,
  sidebarTriggerVariants,
  sidebarVariants,
} from './layout.variants';
import { UiStringTemplateOutletDirective } from '../../core/directives/string-template-outlet/string-template-outlet.directive';
import { mergeClasses } from '../../utils/merge-classes';

@Component({
  selector: 'ui-sidebar',
  imports: [UiStringTemplateOutletDirective, UiIconComponent],
  template: `
    <aside [class]="classes()" [style.width.px]="currentWidth()" [attr.data-collapsed]="uiCollapsed()">
      <div class="flex-1 overflow-auto">
        <ng-content />
      </div>

      @if (uiCollapsible() && !uiTrigger()) {
        <div
          [class]="triggerClasses()"
          (click)="toggleCollapsed()"
          (keydown.{enter,space}.prevent)="toggleCollapsed()"
          tabindex="0"
          role="button"
          [attr.aria-label]="uiCollapsed() ? 'Expand sidebar' : 'Collapse sidebar'"
          [attr.aria-expanded]="!uiCollapsed()"
        >
          <ui-icon [uiType]="chevronIcon()" />
        </div>
      }

      @if (uiCollapsible() && uiTrigger()) {
        <ng-container *uiStringTemplateOutlet="uiTrigger()" />
      }
    </aside>
  `,
  changeDetection: ChangeDetectionStrategy.OnPush,
  encapsulation: ViewEncapsulation.None,
  exportAs: 'uiSidebar',
})
export class SidebarComponent {
  readonly uiWidth = input<string | number>(200);
  readonly uiCollapsedWidth = input<number>(64);
  readonly uiCollapsible = input(false, { transform: booleanAttribute });
  readonly uiCollapsed = input(false, { transform: booleanAttribute });
  readonly uiReverseArrow = input(false, { transform: booleanAttribute });
  readonly uiTrigger = input<TemplateRef<void> | null>(null);
  readonly class = input<ClassValue>('');

  readonly uiCollapsedChange = output<boolean>();

  private readonly internalCollapsed = signal(false);

  constructor() {
    effect(() => {
      this.internalCollapsed.set(this.uiCollapsed());
    });
  }

  protected readonly currentWidth = computed(() => {
    const collapsed = this.uiCollapsed();
    if (collapsed) {
      return this.uiCollapsedWidth();
    }

    const width = this.uiWidth();
    return typeof width === 'number' ? width : parseInt(width, 10);
  });

  protected readonly chevronIcon = computed((): UiIcon => {
    const collapsed = this.uiCollapsed();
    const reverse = this.uiReverseArrow();

    if (reverse) {
      return collapsed ? 'chevron-left' : 'chevron-right';
    }
    return collapsed ? 'chevron-right' : 'chevron-left';
  });

  protected readonly classes = computed(() => mergeClasses(sidebarVariants(), this.class()));

  protected readonly triggerClasses = computed(() => mergeClasses(sidebarTriggerVariants()));

  toggleCollapsed(): void {
    const newState = !this.uiCollapsed();
    this.internalCollapsed.set(newState);
    this.uiCollapsedChange.emit(newState);
  }
}

@Component({
  selector: 'ui-sidebar-group',
  template: `
    <div [class]="classes()">
      <ng-content />
    </div>
  `,
  changeDetection: ChangeDetectionStrategy.OnPush,
  encapsulation: ViewEncapsulation.None,
  exportAs: 'uiSidebarGroup',
})
export class SidebarGroupComponent {
  readonly class = input<ClassValue>('');

  protected readonly classes = computed(() => mergeClasses(sidebarGroupVariants(), this.class()));
}

@Component({
  selector: 'ui-sidebar-group-label',
  template: `
    <div [class]="classes()">
      <ng-content />
    </div>
  `,
  changeDetection: ChangeDetectionStrategy.OnPush,
  encapsulation: ViewEncapsulation.None,
  exportAs: 'uiSidebarGroupLabel',
})
export class SidebarGroupLabelComponent {
  readonly class = input<ClassValue>('');

  protected readonly classes = computed(() => mergeClasses(sidebarGroupLabelVariants(), this.class()));
}
