import {
  booleanAttribute,
  ChangeDetectionStrategy,
  Component,
  computed,
  contentChild,
  effect,
  input,
  type TemplateRef,
  viewChild,
  ViewEncapsulation,
} from '@angular/core';

import type { ClassValue } from 'clsx';

import { UiIdDirective } from '../../core';
import {
  isTemplateRef,
  UiStringTemplateOutletDirective,
} from '../../core/directives/string-template-outlet/string-template-outlet.directive';
import { mergeClasses } from '../../utils/merge-classes';

import {
  inputGroupAddonVariants,
  inputGroupInputVariants,
  inputGroupVariants,
  type UiInputGroupAddonAlignVariants,
  type UiInputGroupAddonPositionVariants,
} from './input-group.variants';
import { UiInputDirective } from '../input/input.directive';
import type { UiInputSizeVariants } from '../input/input.variants';
import { UiLoaderComponent } from '../loader/loader.component';

@Component({
  selector: 'ui-input-group',
  imports: [UiStringTemplateOutletDirective, UiLoaderComponent, UiIdDirective],
  template: `
    <ng-container uiId="input-group" #z="uiId">
      @let addonBefore = uiAddonBefore();
      @if (addonBefore) {
        <div [class]="addonBeforeClasses()" [id]="addonBeforeId()" [attr.aria-disabled]="uiDisabled() || uiLoading()">
          <ng-container *uiStringTemplateOutlet="addonBefore">{{ addonBefore }}</ng-container>
        </div>
      }

      <div [class]="inputWrapperClasses()">
        <ng-content select="input[ui-input], textarea[ui-input]" />

        @if (uiLoading()) {
          <ui-loader uiSize="sm" />
        }
      </div>

      @let addonAfter = uiAddonAfter();
      @if (addonAfter) {
        <div [class]="addonAfterClasses()" [id]="addonAfterId()" [attr.aria-disabled]="uiDisabled() || uiLoading()">
          <ng-container *uiStringTemplateOutlet="addonAfter">{{ addonAfter }}</ng-container>
        </div>
      }
    </ng-container>
  `,
  changeDetection: ChangeDetectionStrategy.OnPush,
  encapsulation: ViewEncapsulation.None,
  host: {
    '[class]': 'classes()',
    '[attr.aria-disabled]': 'uiDisabled() || uiLoading()',
    '[attr.data-disabled]': 'uiDisabled() || uiLoading()',
    '[attr.aria-busy]': 'uiLoading()',
    'data-slot': 'input-group',
    role: 'group',
  },
})
export class UiInputGroupComponent {
  readonly class = input<ClassValue>('');
  readonly uiAddonAfter = input<string | TemplateRef<void>>('');
  readonly uiAddonAlign = input<UiInputGroupAddonAlignVariants>('inline');
  readonly uiAddonBefore = input<string | TemplateRef<void>>('');
  readonly uiDisabled = input(false, { transform: booleanAttribute });
  readonly uiLoading = input(false, { transform: booleanAttribute });
  readonly uiSize = input<UiInputSizeVariants>('default');

  private readonly contentInput = contentChild<UiInputDirective>(UiInputDirective);
  private readonly uniqueId = viewChild<UiIdDirective>('z');

  protected readonly addonBeforeId = computed(() => `${this.uniqueId()?.id() ?? 'input-group'}-addon-before`);
  protected readonly addonAfterId = computed(() => `${this.uniqueId()?.id() ?? 'input-group'}-addon-after`);
  protected readonly isAddonBeforeTemplate = computed(() => isTemplateRef(this.uiAddonBefore()));
  protected readonly classes = computed(() =>
    mergeClasses(
      'w-full',
      inputGroupVariants({
        uiSize: this.uiSize(),
        uiDisabled: this.uiDisabled() || this.uiLoading(),
      }),
      this.class(),
    ),
  );

  protected readonly inputWrapperClasses = computed(() =>
    mergeClasses(
      inputGroupInputVariants({
        uiSize: this.uiSize(),
        uiHasAddonBefore: Boolean(this.uiAddonBefore()),
        uiHasAddonAfter: Boolean(this.uiAddonAfter()),
        uiDisabled: this.uiDisabled() || this.uiLoading(),
      }),
      'relative',
    ),
  );

  protected readonly addonAfterClasses = computed(() => this.addonClasses('after'));
  protected readonly addonBeforeClasses = computed(() =>
    mergeClasses(this.addonClasses('before'), this.isAddonBeforeTemplate() ? 'pr-0.5' : ''),
  );

  constructor() {
    effect(() => {
      const contentInput = this.contentInput();
      const disabled = this.uiDisabled();
      const size = this.uiSize();

      if (size) {
        contentInput?.size.set(size);
      }
      contentInput?.disable(disabled);
      contentInput?.setDataSlot('input-group-control');
    });
  }

  private addonClasses(position: UiInputGroupAddonPositionVariants): string {
    return mergeClasses(
      inputGroupAddonVariants({
        uiAlign: this.uiAddonAlign(),
        uiDisabled: this.uiDisabled() || this.uiLoading(),
        uiPosition: position,
        uiSize: this.uiSize(),
        uiType: this.contentInput()?.getType() ?? 'default',
      }),
    );
  }
}
