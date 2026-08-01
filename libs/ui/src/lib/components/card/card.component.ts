import {
  ChangeDetectionStrategy,
  Component,
  computed,
  input,
  output,
  type TemplateRef,
  viewChild,
  ViewEncapsulation,
} from '@angular/core';

import type { ClassValue } from 'clsx';

import { UiButtonComponent } from '../button/button.component';
import { UiIdDirective, UiStringTemplateOutletDirective } from '../../core';
import { mergeClasses } from '../../utils/merge-classes';

import { cardBodyVariants, cardFooterVariants, cardHeaderVariants, cardVariants } from './card.variants';

@Component({
  selector: 'ui-card',
  imports: [UiStringTemplateOutletDirective, UiButtonComponent, UiIdDirective],
  template: `
    <ng-container uiId="card" #z="uiId">
      @let title = uiTitle();
      @if (title) {
        <div [class]="headerClasses()" data-slot="card-header">
          <div class="leading-none font-semibold" [id]="titleId()" data-slot="card-title">
            <ng-container *uiStringTemplateOutlet="title">{{ title }}</ng-container>
          </div>

          @let description = uiDescription();
          @if (description) {
            <div class="text-muted-foreground text-sm" [id]="descriptionId()" data-slot="card-description">
              <ng-container *uiStringTemplateOutlet="description">{{ description }}</ng-container>
            </div>
          }

          @let action = uiAction();
          @if (action) {
            <button
              ui-button
              type="button"
              uiType="link"
              class="col-start-2 row-span-2 row-start-1 self-start justify-self-end"
              data-slot="card-action"
              (click)="onClick()"
            >
              {{ action }}
            </button>
          }
        </div>
      }

      <div [class]="bodyClasses()" data-slot="card-content">
        <ng-content />
      </div>

      <div [class]="footerClasses()" data-slot="card-footer">
        <ng-content select="[card-footer]" />
      </div>
    </ng-container>
  `,
  styles: `
    [data-slot='card-footer']:empty {
      display: none;
    }
  `,
  changeDetection: ChangeDetectionStrategy.OnPush,
  encapsulation: ViewEncapsulation.None,
  host: {
    'data-slot': 'card',
    '[class]': 'classes()',
    '[attr.aria-labelledby]': 'titleId()',
    '[attr.aria-describedby]': 'descriptionId()',
  },
  exportAs: 'uiCard',
})
export class UiCardComponent {
  private readonly generatedId = viewChild<UiIdDirective>('z');

  readonly class = input<ClassValue>('');
  readonly uiFooterBorder = input(false);
  readonly uiHeaderBorder = input(false);
  readonly uiAction = input('');
  readonly uiDescription = input<string | TemplateRef<void>>();
  readonly uiTitle = input<string | TemplateRef<void>>();

  readonly uiActionClick = output<void>();

  protected readonly titleId = computed(() => {
    const baseId = this.generatedId()?.id();
    return this.uiTitle() && baseId ? `${baseId}-title` : null;
  });

  protected readonly descriptionId = computed(() => {
    const baseId = this.generatedId()?.id();
    return this.uiDescription() && baseId ? `${baseId}-description` : null;
  });

  protected readonly classes = computed(() => mergeClasses(cardVariants(), this.class()));
  protected readonly bodyClasses = computed(() => mergeClasses(cardBodyVariants()));
  protected readonly footerClasses = computed(() =>
    mergeClasses(cardFooterVariants(), this.uiFooterBorder() ? 'border-t' : ''),
  );

  protected readonly headerClasses = computed(() =>
    mergeClasses(cardHeaderVariants(), this.uiHeaderBorder() ? 'border-b' : ''),
  );

  protected onClick(): void {
    this.uiActionClick.emit();
  }
}
