import {
  ChangeDetectionStrategy,
  Component,
  computed,
  contentChildren,
  inject,
  input,
  signal,
  ViewEncapsulation,
} from '@angular/core';

import type { ClassValue } from 'clsx';

import { UiCommandOptionComponent } from './command-option.component';
import { UiCommandComponent } from './command.component';
import { commandGroupHeadingVariants, commandGroupVariants } from './command.variants';
import { mergeClasses } from '../../utils/merge-classes';

export abstract class UiCommandOptionGroup {
  abstract registerOption(option: UiCommandOptionComponent): void;
  abstract unregisterOption(option: UiCommandOptionComponent): void;
}

@Component({
  selector: 'ui-command-option-group',
  template: `
    @if (isGroupVisible()) {
      <div [class]="classes()" role="group">
        @if (uiLabel()) {
          <div [class]="headingClasses()" role="presentation">
            {{ uiLabel() }}
          </div>
        }
        <div role="group">
          <ng-content />
        </div>
      </div>
    }
  `,
  changeDetection: ChangeDetectionStrategy.OnPush,
  encapsulation: ViewEncapsulation.None,
  exportAs: 'uiCommandOptionGroup',
})
export class UiCommandOptionGroupComponent implements UiCommandOptionGroup {
  private readonly commandComponent = inject(UiCommandComponent, { optional: true });
  private readonly optionComponentsAsChildren = contentChildren(UiCommandOptionComponent, { descendants: true });
  private readonly registeredOptionComponents = signal<UiCommandOptionComponent[]>([]);

  readonly uiLabel = input.required<string>();
  readonly class = input<ClassValue>('');

  protected readonly classes = computed(() => mergeClasses(commandGroupVariants({}), this.class()));
  protected readonly headingClasses = computed(() => mergeClasses(commandGroupHeadingVariants({})));
  private readonly optionComponents = computed(() =>
    this.optionComponentsAsChildren().length ? this.optionComponentsAsChildren() : this.registeredOptionComponents(),
  );

  protected readonly isGroupVisible = computed(() => {
    if (!this.commandComponent || !this.optionComponents().length) {
      return true;
    }

    const searchTerm = this.commandComponent.searchTerm();
    // If no search term, show all groups
    if (!searchTerm) {
      return true;
    }

    const filteredOptions = this.commandComponent.filteredOptions();
    // Check if any option in this group is in the filtered list
    return this.optionComponents().some(option => filteredOptions.includes(option));
  });

  registerOption(option: UiCommandOptionComponent) {
    this.registeredOptionComponents.update(current => [...current, option]);
  }

  unregisterOption(option: UiCommandOptionComponent) {
    this.registeredOptionComponents.update(current => current.filter(o => o !== option));
  }
}
