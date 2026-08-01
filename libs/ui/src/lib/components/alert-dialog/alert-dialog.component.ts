import { A11yModule } from '@angular/cdk/a11y';
import { OverlayModule } from '@angular/cdk/overlay';
import {
  BasePortalOutlet,
  CdkPortalOutlet,
  type ComponentPortal,
  PortalModule,
  type TemplatePortal,
} from '@angular/cdk/portal';
import {
  ChangeDetectionStrategy,
  Component,
  type ComponentRef,
  computed,
  ElementRef,
  type EmbeddedViewRef,
  type EventEmitter,
  inject,
  NgModule,
  output,
  type TemplateRef,
  type Type,
  viewChild,
  type ViewContainerRef,
  ViewEncapsulation,
} from '@angular/core';

import type { ClassValue } from 'clsx';

import { UiIdDirective } from '../../core';
import { mergeClasses, noopFn } from '../../utils/merge-classes';

import type { UiAlertDialogRef } from './alert-dialog-ref';
import { UiAlertDialogService } from './alert-dialog.service';
import { alertDialogVariants } from './alert-dialog.variants';
import { UiButtonComponent } from '../button/button.component';

export type OnClickCallback<T> = (instance: T) => false | void | object;

export class UiAlertDialogOptions<T> {
  uiCancelText?: string | null;
  uiClosable?: boolean;
  uiContent?: string | TemplateRef<T> | Type<T>;
  uiCustomClasses?: ClassValue;
  uiData?: object;
  uiDescription?: string;
  uiMaskClosable?: boolean;
  uiOkDestructive?: boolean;
  uiOkDisabled?: boolean;
  uiOkText?: string | null;
  uiOnCancel?: EventEmitter<T> | OnClickCallback<T> = noopFn;
  uiOnOk?: EventEmitter<T> | OnClickCallback<T> = noopFn;
  uiTitle?: string | TemplateRef<T>;
  uiViewContainerRef?: ViewContainerRef;
  uiWidth?: string;
}

@Component({
  selector: 'ui-alert-dialog',
  imports: [OverlayModule, PortalModule, UiButtonComponent, A11yModule, UiIdDirective],
  templateUrl: './alert-dialog.component.html',
  styles: `
    ui-alert-dialog {
      inset: 0;
      margin: auto;
      width: fit-content;
      height: fit-content;
      transform-origin: center center;
      opacity: 1;
      transform: scale(1);
      transition:
        opacity 150ms ease-out,
        transform 150ms ease-out;
    }

    @starting-style {
      ui-alert-dialog {
        opacity: 0;
        transform: scale(0.9);
      }
    }

    ui-alert-dialog.alert-dialog-leave {
      opacity: 0;
      transform: scale(0.9);
      transition:
        opacity 150ms ease-in,
        transform 150ms ease-in;
    }
  `,
  changeDetection: ChangeDetectionStrategy.OnPush,
  encapsulation: ViewEncapsulation.None,
  host: {
    '[class]': 'classes()',
    '[style.width]': 'config.uiWidth ? config.uiWidth : null',
    role: 'alertdialog',
    '[attr.aria-modal]': 'true',
    '[attr.aria-labelledby]': 'titleId()',
    '[attr.aria-describedby]': 'descriptionId()',
    'animate.enter': 'alert-dialog-enter',
    'animate.leave': 'alert-dialog-leave',
  },
  exportAs: 'uiAlertDialog',
})
export class UiAlertDialogComponent<T> extends BasePortalOutlet {
  protected readonly alertDialogId = viewChild<UiIdDirective>('z');
  private readonly host = inject(ElementRef<HTMLElement>);
  protected readonly config = inject(UiAlertDialogOptions<T>);

  protected readonly classes = computed(() => mergeClasses(alertDialogVariants(), this.config.uiCustomClasses));

  protected readonly titleId = computed(() => {
    const baseId = this.alertDialogId()?.id();
    return this.config.uiTitle && baseId ? `${baseId}-title` : null;
  });

  protected readonly descriptionId = computed(() => {
    const baseId = this.alertDialogId()?.id();
    return this.config.uiDescription && baseId ? `${baseId}-description` : null;
  });

  alertDialogRef?: UiAlertDialogRef<T>;

  protected readonly isStringContent = computed(() => typeof this.config.uiContent === 'string');

  readonly portalOutlet = viewChild.required(CdkPortalOutlet);

  okTriggered = output<void>();
  cancelTriggered = output<void>();

  constructor() {
    super();
  }

  getNativeElement(): HTMLElement {
    return this.host.nativeElement;
  }

  attachComponentPortal<T>(portal: ComponentPortal<T>): ComponentRef<T> {
    if (this.portalOutlet()?.hasAttached()) {
      throw new Error('Attempting to attach alert dialog content after content is already attached');
    }
    return this.portalOutlet()?.attachComponentPortal(portal);
  }

  attachTemplatePortal<C>(portal: TemplatePortal<C>): EmbeddedViewRef<C> {
    if (this.portalOutlet()?.hasAttached()) {
      throw new Error('Attempting to attach alert dialog content after content is already attached');
    }

    return this.portalOutlet()?.attachTemplatePortal(portal);
  }

  onOkClick() {
    this.okTriggered.emit();
  }

  onCancelClick() {
    this.cancelTriggered.emit();
  }
}

@NgModule({
  imports: [UiButtonComponent, UiAlertDialogComponent, OverlayModule, PortalModule, A11yModule],
  providers: [UiAlertDialogService],
})
export class UiAlertDialogModule {}
