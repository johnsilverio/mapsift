import {
  ChangeDetectionStrategy,
  Component,
  computed,
  contentChild,
  contentChildren,
  inject,
  input,
  TemplateRef,
  ViewEncapsulation,
} from '@angular/core';
import { type Params, RouterLink } from '@angular/router';

import type { ClassValue } from 'clsx';

import {
  breadcrumbEllipsisVariants,
  breadcrumbItemVariants,
  breadcrumbListVariants,
  breadcrumbVariants,
  type UiBreadcrumbAlignVariants,
  type UiBreadcrumbEllipsisColorVariants,
  type UiBreadcrumbSizeVariants,
  type UiBreadcrumbWrapVariants,
} from './breadcrumb.variants';
import { UiIconComponent } from '../icon';
import { UiStringTemplateOutletDirective } from '../../core/directives/string-template-outlet/string-template-outlet.directive';
import { mergeClasses } from '../../utils/merge-classes';

@Component({
  selector: 'ui-breadcrumb-ellipsis, [ui-breadcrumb-ellipsis]',
  imports: [UiIconComponent],
  template: `
    <ui-icon uiType="ellipsis" />
  `,
  changeDetection: ChangeDetectionStrategy.OnPush,
  encapsulation: ViewEncapsulation.None,
  host: {
    '[class]': 'classes()',
    'aria-hidden': 'true',
    role: 'presentation',
  },
  exportAs: 'uiBreadcrumbEllipsis',
})
export class UiBreadcrumbEllipsisComponent {
  readonly uiColor = input<UiBreadcrumbEllipsisColorVariants>('muted');

  readonly class = input<ClassValue>('');
  protected readonly classes = computed(() =>
    mergeClasses(breadcrumbEllipsisVariants({ uiColor: this.uiColor() }), this.class()),
  );
}

@Component({
  selector: 'ui-breadcrumb-item, [ui-breadcrumb-item]',
  imports: [UiStringTemplateOutletDirective, UiIconComponent, RouterLink],
  template: `
    <ng-template #itemContent><ng-content /></ng-template>

    <li [class]="classes()">
      @if (isEllipsis()) {
        <ng-container *uiStringTemplateOutlet="itemContent" />
      } @else {
        <a
          class="flex items-center gap-1.5"
          [routerLink]="routerLink()"
          [queryParams]="queryParams()"
          [fragment]="fragment()"
        >
          <ng-container *uiStringTemplateOutlet="itemContent" />
        </a>
      }
    </li>

    @if (!isLast()) {
      <li aria-hidden="true" role="presentation" [class]="separatorClasses()" (click)="$event.stopPropagation()">
        @if (isTemplate(separator())) {
          <ng-container *uiStringTemplateOutlet="separator()" />
        } @else if (separator()) {
          {{ separator() }}
        } @else {
          <ui-icon uiType="chevron-right" />
        }
      </li>
    }
  `,
  changeDetection: ChangeDetectionStrategy.OnPush,
  encapsulation: ViewEncapsulation.None,
  host: {
    class: 'inline-flex items-center gap-1.5',
  },
  hostDirectives: [
    {
      directive: RouterLink,
      inputs: [
        'routerLink',
        'queryParams',
        'fragment',
        'queryParamsHandling',
        'state',
        'relativeTo',
        'preserveFragment',
        'skipLocationChange',
        'replaceUrl',
      ],
    },
  ],
  exportAs: 'uiBreadcrumbItem',
})
export class UiBreadcrumbItemComponent {
  private readonly breadcrumbComponent = inject(UiBreadcrumbComponent);

  private readonly content = contentChild(UiBreadcrumbEllipsisComponent);
  /*
    These three inputs are affecting the link so we need them for anchor link.
    They are not part of component API in any sense as that is done through
    host directive.
  */
  readonly routerLink = input<string[]>([]);
  readonly queryParams = input<Params | null | undefined>();
  readonly fragment = input<string | undefined>();

  readonly class = input<ClassValue>('');

  protected readonly separator = computed(() => this.breadcrumbComponent.uiSeparator());
  protected readonly isLast = computed<boolean>(() => this === this.breadcrumbComponent.items().at(-1));
  protected readonly isEllipsis = computed<boolean>(() => this.content() !== undefined);

  protected readonly classes = computed(() => mergeClasses(breadcrumbItemVariants(), this.class()));
  protected readonly separatorClasses = computed(() => 'text-muted-foreground [&_svg]:size-3.5');

  protected isTemplate(value: string | TemplateRef<void>): value is TemplateRef<void> {
    return value instanceof TemplateRef;
  }
}

@Component({
  selector: 'ui-breadcrumb, [ui-breadcrumb]',
  template: `
    <nav aria-label="breadcrumb" [class]="navClasses()">
      <ol [class]="listClasses()">
        <ng-content />
      </ol>
    </nav>
  `,
  changeDetection: ChangeDetectionStrategy.OnPush,
  encapsulation: ViewEncapsulation.None,
  exportAs: 'uiBreadcrumb',
})
export class UiBreadcrumbComponent {
  readonly uiSize = input<UiBreadcrumbSizeVariants>('md');
  readonly uiAlign = input<UiBreadcrumbAlignVariants>('start');
  readonly uiWrap = input<UiBreadcrumbWrapVariants>('wrap');
  readonly uiSeparator = input<string | TemplateRef<void>>('');

  readonly class = input<ClassValue>('');

  readonly items = contentChildren(UiBreadcrumbItemComponent);

  protected readonly navClasses = computed(() =>
    mergeClasses(breadcrumbVariants({ uiSize: this.uiSize() }), this.class()),
  );

  protected readonly listClasses = computed(() =>
    breadcrumbListVariants({ uiAlign: this.uiAlign(), uiWrap: this.uiWrap() }),
  );
}
