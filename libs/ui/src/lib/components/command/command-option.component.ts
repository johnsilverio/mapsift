import {
  booleanAttribute,
  ChangeDetectionStrategy,
  Component,
  computed,
  effect,
  ElementRef,
  inject,
  input,
  signal,
  ViewEncapsulation,
} from '@angular/core';

import type { ClassValue } from 'clsx';

import type { UiCommandOptionGroupComponent } from './command-option-group.component';
import { UiCommandComponent } from './command.component';
import {
  commandItemVariants,
  commandShortcutVariants,
  type UiCommandItemVariants,
} from './command.variants';
import { UiIconComponent, type UiIcon } from '../icon';
import { mergeClasses } from '../../utils/merge-classes';

@Component({
  selector: 'ui-command-option',
  imports: [UiIconComponent],
  template: `
    @if (isOptionVisible()) {
      <div
        [class]="classes()"
        [attr.role]="'option'"
        [attr.aria-selected]="isSelected()"
        [attr.data-selected]="isSelected()"
        [attr.data-disabled]="uiDisabled()"
        [attr.tabindex]="0"
        (click)="onClick()"
        (keydown.{enter,space}.prevent)="onClick()"
        (mouseenter)="onMouseEnter()"
      >
        @if (uiIcon()) {
          <div ui-icon [uiType]="uiIcon()!" class="mr-2 flex shrink-0 items-center justify-center"></div>
        }
        <span class="flex-1">{{ uiLabel() }}</span>
        @if (uiShortcut()) {
          <span [class]="shortcutClasses()">{{ uiShortcut() }}</span>
        }
      </div>
    }
  `,
  changeDetection: ChangeDetectionStrategy.OnPush,
  encapsulation: ViewEncapsulation.None,
  exportAs: 'uiCommandOption',
})
export class UiCommandOptionComponent {
  private readonly elementRef = inject(ElementRef);
  private readonly parentCommandComponent = inject(UiCommandComponent, { optional: true });

  readonly uiValue = input.required<unknown>();
  readonly uiLabel = input.required<string>();
  readonly uiCommand = input<string>('');
  readonly uiIcon = input<UiIcon>();
  readonly uiShortcut = input<string>('');
  readonly uiDisabled = input(false, { transform: booleanAttribute });
  readonly variant = input<UiCommandItemVariants>('default');
  readonly class = input<ClassValue>('');
  readonly parentCommand = input<UiCommandComponent | null>(null);
  readonly commandGroup = input<UiCommandOptionGroupComponent | null>(null);

  readonly isSelected = signal(false);

  protected readonly classes = computed(() => {
    const baseClasses = commandItemVariants({ variant: this.variant() });
    const selectedClasses = this.isSelected() ? 'bg-accent text-accent-foreground' : '';
    return mergeClasses(baseClasses, selectedClasses, this.class());
  });

  protected readonly shortcutClasses = computed(() => mergeClasses(commandShortcutVariants()));

  private get commandComponent() {
    let parent = this.parentCommand();
    parent ||= this.parentCommandComponent;
    return parent;
  }

  protected readonly isOptionVisible = computed(() => {
    const parent = this.commandComponent;

    if (!parent) {
      return true;
    }
    /*
      If no search term, show this option, otherwise check
      if this option is included in the filtered list
     */
    return !parent.searchTerm() || parent.filteredOptions().includes(this);
  });

  constructor() {
    effect(onCleanup => {
      const cmd = this.parentCommand();
      const grp = this.commandGroup();

      if (cmd) {
        cmd.registerOption(this);
        onCleanup(() => cmd.unregisterOption(this));
      }

      if (grp) {
        grp.registerOption(this);
        onCleanup(() => grp.unregisterOption(this));
      }
    });
  }

  onClick() {
    if (this.uiDisabled()) {
      return;
    }

    this.commandComponent?.selectOption(this);
  }

  onMouseEnter() {
    if (this.uiDisabled()) {
      return;
    }
    // Visual feedback for hover
  }

  setSelected(selected: boolean) {
    this.isSelected.set(selected);
  }

  focus() {
    const element = this.elementRef.nativeElement;
    element.focus();
    element.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
  }
}
