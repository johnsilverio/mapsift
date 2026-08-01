import { NgTemplateOutlet } from '@angular/common';
import {
  booleanAttribute,
  ChangeDetectionStrategy,
  Component,
  computed,
  input,
  model,
  type TemplateRef,
  ViewEncapsulation,
} from '@angular/core';

import type { ClassValue } from 'clsx';

import {
  UiButtonComponent,
  type UiButtonSizeVariants,
  type UiButtonTypeVariants,
} from '../button';
import { UiIconComponent } from '../icon';
import {
  paginationContentVariants,
  paginationEllipsisVariants,
  paginationNextVariants,
  paginationPreviousVariants,
  paginationVariants,
} from './pagination.variants';
import { mergeClasses } from '../../utils/merge-classes';

@Component({
  selector: 'ul[ui-pagination-content]',
  template: `
    <ng-content />
  `,
  changeDetection: ChangeDetectionStrategy.OnPush,
  encapsulation: ViewEncapsulation.None,
  host: {
    'data-slot': 'pagination-content',
    '[class]': 'classes()',
  },
  exportAs: 'uiPaginationContent',
})
export class UiPaginationContentComponent {
  readonly class = input<ClassValue>('');

  protected readonly classes = computed(() => mergeClasses(paginationContentVariants(), this.class()));
}

@Component({
  selector: 'li[ui-pagination-item]',
  template: `
    <ng-content />
  `,
  changeDetection: ChangeDetectionStrategy.OnPush,
  encapsulation: ViewEncapsulation.None,
  host: {
    'data-slot': 'pagination-item',
  },
  exportAs: 'uiPaginationItem',
})
export class UiPaginationItemComponent {}
// Structural wrapper component for pagination items (<li>). No inputs required.

@Component({
  selector: 'button[ui-pagination-button], a[ui-pagination-button]',
  imports: [UiButtonComponent],
  template: `
    <ui-button
      [attr.data-active]="uiActive() || null"
      [class]="class()"
      [uiDisabled]="uiDisabled()"
      [uiSize]="uiSize()"
      [uiType]="uiType()"
    >
      <ng-content />
    </ui-button>
  `,
  changeDetection: ChangeDetectionStrategy.OnPush,
  encapsulation: ViewEncapsulation.None,
  host: {
    'data-slot': 'pagination-button',
  },
  exportAs: 'uiPaginationButton',
})
export class UiPaginationButtonComponent {
  readonly class = input<ClassValue>('');
  readonly uiActive = input(false, { transform: booleanAttribute });
  readonly uiDisabled = input(false, { transform: booleanAttribute });
  readonly uiSize = input<UiButtonSizeVariants>('default');

  protected readonly uiType = computed<UiButtonTypeVariants>(() => (this.uiActive() ? 'outline' : 'ghost'));
}

@Component({
  selector: 'ui-pagination-previous',
  imports: [UiPaginationButtonComponent, UiIconComponent],
  template: `
    <button
      type="button"
      ui-pagination-button
      [attr.disabled]="uiDisabled() ? '' : null"
      [class]="classes()"
      [uiSize]="uiSize()"
      [uiDisabled]="uiDisabled()"
    >
      <span class="sr-only">To previous page</span>
      <ui-icon uiType="chevron-left" aria-hidden="true" />
      <span class="hidden sm:block" aria-hidden="true">Previous</span>
    </button>
  `,
  changeDetection: ChangeDetectionStrategy.OnPush,
  encapsulation: ViewEncapsulation.None,
  exportAs: 'uiPaginationPrevious',
})
export class UiPaginationPreviousComponent {
  readonly class = input<ClassValue>('');
  readonly uiDisabled = input(false, { transform: booleanAttribute });
  readonly uiSize = input<UiButtonSizeVariants>('default');

  protected readonly classes = computed(() => mergeClasses(paginationPreviousVariants(), this.class()));
}

@Component({
  selector: 'ui-pagination-next',
  imports: [UiPaginationButtonComponent, UiIconComponent],
  template: `
    <button
      type="button"
      ui-pagination-button
      [attr.disabled]="uiDisabled() ? '' : null"
      [class]="classes()"
      [uiDisabled]="uiDisabled()"
      [uiSize]="uiSize()"
    >
      <span class="sr-only">To next page</span>
      <span class="hidden sm:block" aria-hidden="true">Next</span>
      <ui-icon uiType="chevron-right" aria-hidden="true" />
    </button>
  `,
  changeDetection: ChangeDetectionStrategy.OnPush,
  encapsulation: ViewEncapsulation.None,
  exportAs: 'uiPaginationNext',
})
export class UiPaginationNextComponent {
  readonly class = input<ClassValue>('');
  readonly uiDisabled = input(false, { transform: booleanAttribute });
  readonly uiSize = input<UiButtonSizeVariants>('default');

  protected readonly classes = computed(() => mergeClasses(paginationNextVariants(), this.class()));
}

@Component({
  selector: 'ui-pagination-ellipsis',
  imports: [UiIconComponent],
  template: `
    <ui-icon uiType="ellipsis" aria-hidden="true" />
  `,
  changeDetection: ChangeDetectionStrategy.OnPush,
  encapsulation: ViewEncapsulation.None,
  host: {
    '[class]': 'classes()',
    'aria-hidden': 'true',
  },
  exportAs: 'uiPaginationEllipsis',
})
export class UiPaginationEllipsisComponent {
  readonly class = input<ClassValue>('');

  protected readonly classes = computed(() => mergeClasses(paginationEllipsisVariants(), this.class()));
}

@Component({
  selector: 'ui-pagination',
  imports: [
    UiPaginationContentComponent,
    UiPaginationItemComponent,
    UiPaginationButtonComponent,
    UiPaginationPreviousComponent,
    UiPaginationNextComponent,
    NgTemplateOutlet,
  ],
  template: `
    @if (uiContent()) {
      <ng-container *ngTemplateOutlet="uiContent()" />
    } @else {
      <ul ui-pagination-content>
        <li ui-pagination-item>
          @let pagePrevious = Math.max(1, uiPageIndex() - 1);
          <ui-pagination-previous
            [uiSize]="uiSize()"
            [uiDisabled]="uiDisabled() || uiPageIndex() === 1"
            (click)="goToPage(pagePrevious)"
          />
        </li>

        @for (page of pages(); track page) {
          <li ui-pagination-item>
            <button
              ui-pagination-button
              type="button"
              class="focus-visible:rounded-md"
              [attr.aria-current]="page === uiPageIndex() ? 'page' : null"
              [attr.aria-disabled]="uiDisabled() || null"
              [uiActive]="page === uiPageIndex()"
              [uiDisabled]="uiDisabled()"
              [uiSize]="uiSize()"
              (click)="goToPage(page)"
            >
              <span class="sr-only">{{ pages().length === page ? 'To last page, page' : 'To page' }}</span>
              {{ page }}
            </button>
          </li>
        }

        <li ui-pagination-item>
          @let pageNext = Math.min(uiPageIndex() + 1, uiTotal());
          <ui-pagination-next
            [uiSize]="uiSize()"
            [uiDisabled]="uiDisabled() || uiPageIndex() === uiTotal()"
            (click)="goToPage(pageNext)"
          />
        </li>
      </ul>
    }
  `,
  changeDetection: ChangeDetectionStrategy.OnPush,
  encapsulation: ViewEncapsulation.None,
  host: {
    role: 'group',
    '[attr.aria-label]': 'uiAriaLabel()',
    'data-slot': 'pagination',
    '[class]': 'classes()',
  },
  exportAs: 'uiPagination',
})
export class UiPaginationComponent {
  readonly uiPageIndex = model<number>(1);
  readonly uiTotal = input<number>(1);
  readonly uiSize = input<UiButtonSizeVariants>('default');
  readonly uiDisabled = input(false, { transform: booleanAttribute });
  readonly uiContent = input<TemplateRef<void> | undefined>();
  readonly uiAriaLabel = input('Pagination');

  readonly class = input<ClassValue>('');

  // `uiPageIndex` is a model, so Angular already exposes `uiPageIndexChange` and emits it on
  // every `set`. Declaring the output again shadowed that one, which the v22 compiler rejects
  // outright (NG1054), and it also made every page change arrive at the consumer twice.
  readonly Math = Math;

  protected readonly classes = computed(() => mergeClasses(paginationVariants(), this.class()));
  readonly pages = computed<number[]>(() => Array.from({ length: Math.max(0, this.uiTotal()) }, (_, i) => i + 1));

  goToPage(page: number): void {
    if (!this.uiDisabled() && page !== this.uiPageIndex()) {
      this.uiPageIndex.set(page);
    }
  }
}
