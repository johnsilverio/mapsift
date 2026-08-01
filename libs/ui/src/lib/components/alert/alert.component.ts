import { ChangeDetectionStrategy, Component, computed, input, TemplateRef, ViewEncapsulation } from '@angular/core';

import type { ClassValue } from 'clsx';

import { UiStringTemplateOutletDirective } from '../../core/directives/string-template-outlet/string-template-outlet.directive';
import { mergeClasses } from '../../utils/merge-classes';

import {
  alertDescriptionVariants,
  alertIconVariants,
  alertTitleVariants,
  alertVariants,
  type UiAlertTypeVariants,
} from './alert.variants';
import { UiIconComponent } from '../icon/icon.component';
import type { UiIcon } from '../icon/icons';

@Component({
  selector: 'ui-alert, [ui-alert]',
  imports: [UiIconComponent, UiStringTemplateOutletDirective],
  standalone: true,
  template: `
    @if (uiIcon() || iconName()) {
      <span [class]="iconClasses()" data-slot="alert-icon">
        <ng-container *uiStringTemplateOutlet="uiIcon()">
          <ui-icon [uiType]="iconName()!" />
        </ng-container>
      </span>
    }

    <div class="flex-1">
      @if (uiTitle()) {
        <div [class]="titleClasses()" data-slot="alert-title">
          <ng-container *uiStringTemplateOutlet="uiTitle()">{{ uiTitle() }}</ng-container>
        </div>
      }

      @if (uiDescription()) {
        <div [class]="descriptionClasses()" data-slot="alert-description">
          <ng-container *uiStringTemplateOutlet="uiDescription()">{{ uiDescription() }}</ng-container>
        </div>
      }
    </div>
  `,
  changeDetection: ChangeDetectionStrategy.OnPush,
  encapsulation: ViewEncapsulation.None,
  host: {
    role: 'alert',
    '[class]': 'classes()',
    '[attr.data-slot]': '"alert"',
  },
  exportAs: 'uiAlert',
})
export class UiAlertComponent {
  readonly class = input<ClassValue>('');
  readonly uiTitle = input<string | TemplateRef<void>>('');
  readonly uiDescription = input<string | TemplateRef<void>>('');
  readonly uiIcon = input<UiIcon | TemplateRef<void>>();
  readonly uiType = input<UiAlertTypeVariants>('default');

  protected readonly classes = computed(() => mergeClasses(alertVariants({ uiType: this.uiType() }), this.class()));

  protected readonly iconClasses = computed(() => alertIconVariants());

  protected readonly titleClasses = computed(() => alertTitleVariants());

  protected readonly descriptionClasses = computed(() => alertDescriptionVariants({ uiType: this.uiType() }));

  protected readonly iconName = computed((): UiIcon | null => {
    const customIcon = this.uiIcon();
    if (customIcon && !(customIcon instanceof TemplateRef)) {
      return customIcon;
    }

    if (this.uiType() === 'destructive') {
      return 'circle-alert';
    }

    return null;
  });
}
