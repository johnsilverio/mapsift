import { NgTemplateOutlet } from '@angular/common';
import {
  afterNextRender,
  booleanAttribute,
  ChangeDetectionStrategy,
  Component,
  computed,
  ElementRef,
  forwardRef,
  inject,
  Injector,
  input,
  output,
  runInInjectionContext,
  signal,
  viewChild,
  ViewEncapsulation,
} from '@angular/core';
import { type ControlValueAccessor, FormsModule, NG_VALUE_ACCESSOR } from '@angular/forms';

import type { ClassValue } from 'clsx';

import { UiButtonComponent, type UiButtonTypeVariants } from '../button';
import { comboboxVariants, type UiComboboxWidthVariants } from './combobox.variants';
import {
  UiCommandComponent,
  UiCommandEmptyComponent,
  UiCommandInputComponent,
  UiCommandListComponent,
  UiCommandOptionComponent,
  UiCommandOptionGroupComponent,
  type UiCommandOption,
} from '../command';
import { UiEmptyComponent } from '../empty';
import { UiIconComponent, type UiIcon } from '../icon';
import { UiPopoverComponent, UiPopoverDirective } from '../popover';
import { mergeClasses } from '../../utils/merge-classes';

export interface UiComboboxOption {
  value: string;
  label: string;
  disabled?: boolean;
  icon?: UiIcon;
}

export interface UiComboboxGroup {
  label?: string;
  options: UiComboboxOption[];
}

@Component({
  selector: 'ui-combobox',
  imports: [
    FormsModule,
    NgTemplateOutlet,
    UiButtonComponent,
    UiCommandComponent,
    UiCommandInputComponent,
    UiCommandListComponent,
    UiCommandEmptyComponent,
    UiCommandOptionComponent,
    UiCommandOptionGroupComponent,
    UiPopoverDirective,
    UiPopoverComponent,
    UiEmptyComponent,
    UiIconComponent,
  ],
  template: `
    <button
      type="button"
      ui-button
      uiPopover
      role="combobox"
      [uiContent]="popoverContent"
      [uiType]="buttonVariant()"
      [class]="buttonClasses()"
      [uiDisabled]="disabled()"
      [attr.aria-expanded]="open()"
      [attr.aria-haspopup]="'listbox'"
      [attr.aria-controls]="'combobox-listbox'"
      [attr.aria-label]="ariaLabel() || 'Select option'"
      [attr.aria-describedby]="ariaDescribedBy()"
      [attr.aria-autocomplete]="searchable() ? 'list' : 'none'"
      [attr.aria-activedescendant]="null"
      (uiVisibleChange)="setOpen($event)"
      #popoverTrigger
    >
      <span class="flex-1 truncate text-left">
        {{ displayValue() ?? placeholder() }}
      </span>
      <ui-icon uiType="chevrons-up-down" class="ml-2 shrink-0 opacity-50" />
    </button>

    <ng-template #popoverContent>
      <ui-popover [class]="popoverClasses()">
        <ui-command class="min-h-auto" (uiCommandSelected)="handleSelect($event)" #commandRef>
          @if (searchable()) {
            <ui-command-input [placeholder]="searchPlaceholder()" #commandInputRef />
          }

          <ui-command-list id="combobox-listbox" role="listbox">
            @if (emptyText()) {
              <ui-command-empty>
                <ui-empty [uiDescription]="emptyText()" />
              </ui-command-empty>
            }

            @for (group of groups(); track group.label ?? $index) {
              @if (group.label) {
                <ui-command-option-group [uiLabel]="group.label" #commandGroup>
                  @for (option of group.options; track option.value) {
                    <ng-container
                      [ngTemplateOutlet]="commandOption"
                      [ngTemplateOutletContext]="{
                        $implicit: option,
                        commandInstance: commandRef,
                        groupInstance: commandGroup,
                      }"
                    />
                  }
                </ui-command-option-group>
              } @else {
                @for (option of group.options; track option.value) {
                  <ng-container
                    [ngTemplateOutlet]="commandOption"
                    [ngTemplateOutletContext]="{
                      $implicit: option,
                      commandInstance: commandRef,
                    }"
                  />
                }
              }
            } @empty {
              @if (options().length > 0) {
                @for (option of options(); track option.value) {
                  <ng-container
                    [ngTemplateOutlet]="commandOption"
                    [ngTemplateOutletContext]="{
                      $implicit: option,
                      commandInstance: commandRef,
                    }"
                  />
                }
              }
            }
          </ui-command-list>
        </ui-command>
      </ui-popover>
    </ng-template>

    <ng-template #commandOption let-option let-cmd="commandInstance" let-grp="groupInstance">
      <ui-command-option
        [uiValue]="option.value"
        [uiLabel]="option.label"
        [uiDisabled]="option.disabled ?? false"
        [uiIcon]="option.icon"
        [parentCommand]="cmd"
        [commandGroup]="grp"
        [attr.aria-selected]="option.value === currentValue()"
      >
        {{ option.label }}
        @if (option.value === currentValue()) {
          <ui-icon uiType="check" class="ml-auto" />
        }
      </ui-command-option>
    </ng-template>
  `,
  providers: [
    {
      provide: NG_VALUE_ACCESSOR,
      useExisting: forwardRef(() => UiComboboxComponent),
      multi: true,
    },
  ],
  changeDetection: ChangeDetectionStrategy.OnPush,
  encapsulation: ViewEncapsulation.None,
  host: {
    '[class]': 'classes()',
    '(document:keydown.escape)': 'onDocumentKeyDown($event)',
    '(keydown.escape.prevent-with-stop)': 'onKeyDownEscape()',
    '(keydown.{arrowdown,arrowup,enter,home,end,pageup,pagedown,space}.prevent)': 'onKeyDown($event)',
    '(keydown.tab)': 'onKeyDown($event)',
  },
  exportAs: 'uiCombobox',
})
export class UiComboboxComponent implements ControlValueAccessor {
  private readonly injector = inject(Injector);

  readonly class = input<ClassValue>('');
  readonly buttonVariant = input<UiButtonTypeVariants>('outline');
  readonly uiWidth = input<UiComboboxWidthVariants>('default');
  readonly placeholder = input<string>('Select...');
  readonly searchPlaceholder = input<string>('Search...');
  readonly emptyText = input<string>('No results found.');
  readonly disabled = input(false, { transform: booleanAttribute });
  readonly searchable = input(true, { transform: booleanAttribute });
  readonly value = input<string | null>(null);
  readonly options = input<UiComboboxOption[]>([]);
  readonly groups = input<UiComboboxGroup[]>([]);
  readonly ariaLabel = input<string>('');
  readonly ariaDescribedBy = input<string>('');

  readonly uiValueChange = output<string | null>();
  readonly uiComboSelected = output<UiComboboxOption>();

  readonly popoverDirective = viewChild.required('popoverTrigger', { read: UiPopoverDirective });
  readonly buttonRef = viewChild.required('popoverTrigger', { read: ElementRef });
  readonly commandRef = viewChild('commandRef', { read: UiCommandComponent });
  readonly commandInputRef = viewChild('commandInputRef', { read: UiCommandInputComponent });

  protected readonly open = signal(false);
  protected readonly internalValue = signal<string | null>(null);

  protected readonly classes = computed(() =>
    mergeClasses(
      comboboxVariants({
        uiWidth: this.uiWidth(),
      }),
      this.class(),
    ),
  );

  protected readonly buttonClasses = computed(() => 'w-full justify-between');

  protected readonly popoverClasses = computed(() => {
    const widthClass = this.uiWidth() === 'full' ? 'w-full' : comboboxVariants({ uiWidth: this.uiWidth() });
    return `${widthClass} p-0`;
  });

  protected readonly currentValue = computed(() => this.value() ?? this.internalValue());

  protected readonly displayValue = computed(() => {
    const currentValue = this.currentValue();
    if (!currentValue) {
      return null;
    }

    // Search in groups first
    if (this.groups().length) {
      for (const group of this.groups()) {
        const option = group.options.find(opt => opt.value === currentValue);
        if (option) {
          return option.label;
        }
      }
    }

    // Then search in flat options
    const option = this.options().find(opt => opt.value === currentValue);
    return option?.label ?? null;
  });

  private onChange: (value: string | null) => void = () => {
    // ControlValueAccessor implementation
  };

  private onTouched: () => void = () => {
    // ControlValueAccessor implementation
  };

  setOpen(open: boolean) {
    this.open.set(open);
    if (open) {
      runInInjectionContext(this.injector, () =>
        afterNextRender(() => {
          const commandRef = this.commandRef();
          if (commandRef) {
            // Refresh options to ensure they're detected
            commandRef.refreshOptions();
            // Focus on search input if searchable, otherwise on command component
            if (this.searchable()) {
              this.commandInputRef()?.focus();
            } else {
              commandRef.focus();
            }
          }
        }),
      );
    }
  }

  handleSelect(commandOption: UiCommandOption) {
    const selectedValue = commandOption.value as string;

    // Toggle behavior - if same value is selected, clear it
    const newValue = selectedValue === this.currentValue() ? null : selectedValue;

    this.internalValue.set(newValue);
    this.onChange(newValue);
    this.uiValueChange.emit(newValue);

    // Emit the combobox option if we have a selection
    if (newValue) {
      let selectedOption: UiComboboxOption | undefined;

      if (this.groups().length > 0) {
        for (const group of this.groups()) {
          selectedOption = group.options.find(opt => opt.value === newValue);
          if (selectedOption) {
            break;
          }
        }
      } else {
        selectedOption = this.options().find(opt => opt.value === newValue);
      }

      if (selectedOption) {
        this.uiComboSelected.emit(selectedOption);
      }
    }

    // Close the popover
    this.popoverDirective().hide();

    // Return focus to the combobox button after selection
    this.buttonRef().nativeElement.focus();
  }

  onKeyDownEscape(): void {
    if (this.open()) {
      this.popoverDirective().hide();
      this.buttonRef().nativeElement.focus();
    } else if (this.currentValue()) {
      this.internalValue.set(null);
      this.onChange(null);
      this.uiValueChange.emit(null);
    }
  }

  onKeyDown(e: Event) {
    if (this.disabled()) {
      return;
    }

    const { key, ctrlKey, altKey, metaKey } = e as KeyboardEvent;

    // Handle different keyboard events based on combobox state
    if (this.open()) {
      // When popover is open
      switch (key) {
        case 'Tab':
          // Allow tab to close and move to next element
          this.popoverDirective().hide();
          break;
        case 'ArrowDown':
        case 'ArrowUp':
        case 'Enter':
        case 'Home':
        case 'End':
        case 'PageUp':
        case 'PageDown':
          // Forward navigation to command component
          this.commandRef()?.onKeyDown(e as KeyboardEvent);
          break;
      }
    } else {
      // When popover is closed
      switch (key) {
        case 'ArrowDown':
        case 'ArrowUp':
        case 'Enter':
        case ' ': // Space key
          this.popoverDirective().show();
          break;
        default:
          // For searchable comboboxes, open and start typing
          if (this.searchable() && key.length === 1 && !ctrlKey && !altKey && !metaKey) {
            this.popoverDirective().show();
            // Let the command input handle the character after opening
            runInInjectionContext(this.injector, () =>
              afterNextRender(() => {
                const inputElement = this.commandInputRef();
                if (inputElement) {
                  inputElement.searchInput().nativeElement.value = key;
                  inputElement.updateParentComponents(key);
                  inputElement.focus();
                }
              }),
            );
          }
          break;
      }
    }
  }

  // needed when component loses focus by keyboard.
  onDocumentKeyDown(event: Event) {
    // Close on Escape from anywhere when this combobox is open
    if (this.open()) {
      const target = event.target as Element;
      const buttonElement = this.buttonRef().nativeElement;
      // Only handle if not already handled by the component itself
      if (!buttonElement.contains(target)) {
        this.popoverDirective().hide();
        this.buttonRef().nativeElement.focus();
      }
    }
  }

  // ControlValueAccessor implementation
  writeValue(value: string | null): void {
    this.internalValue.set(value);
  }

  registerOnChange(fn: (value: string | null) => void): void {
    this.onChange = fn;
  }

  registerOnTouched(fn: () => void): void {
    this.onTouched = fn;
  }
}
