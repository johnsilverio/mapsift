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
} from '@angular/core';

import { mergeClasses, noopFn } from '../../utils/merge-classes';

import type { UiDialogRef } from './dialog-ref';
import { UiDialogService } from './dialog.service';
import { dialogVariants } from './dialog.variants';
import { UiButtonComponent } from '../button/button.component';
import { UiIconComponent } from '../icon/icon.component';
import type { UiIcon } from '../icon/icons';

// Used by the NgModule provider definition

export type OnClickCallback<T> = (instance: T) => false | void | object;
export class UiDialogOptions<T, U> {
  uiCancelIcon?: UiIcon;
  uiCancelText?: string | null;
  uiClosable?: boolean;
  uiContent?: string | TemplateRef<T> | Type<T>;
  uiCustomClasses?: string;
  uiData?: U;
  uiDescription?: string;
  uiHideFooter?: boolean;
  uiMaskClosable?: boolean;
  uiOkDestructive?: boolean;
  uiOkDisabled?: boolean;
  uiOkIcon?: UiIcon;
  uiOkText?: string | null;
  uiOnCancel?: EventEmitter<T> | OnClickCallback<T> = noopFn;
  uiOnOk?: EventEmitter<T> | OnClickCallback<T> = noopFn;
  uiTitle?: string | TemplateRef<T>;
  uiViewContainerRef?: ViewContainerRef;
  uiWidth?: string;
}

@Component({
  selector: 'ui-dialog',
  imports: [OverlayModule, PortalModule, UiButtonComponent, UiIconComponent],
  template: `
    @if (config.uiClosable || config.uiClosable === undefined) {
      <button
        type="button"
        data-testid="ui-close-header-button"
        ui-button
        uiType="ghost"
        uiSize="sm"
        class="absolute top-1 right-1"
        (click)="onCloseClick()"
      >
        <ui-icon uiType="x" />
      </button>
    }

    @if (config.uiTitle || config.uiDescription) {
      <header class="flex flex-col space-y-1.5 text-center sm:text-left">
        @if (config.uiTitle) {
          <h4 data-testid="ui-title" class="text-lg leading-none font-semibold tracking-tight">{{ config.uiTitle }}</h4>

          @if (config.uiDescription) {
            <p data-testid="ui-description" class="text-muted-foreground text-sm">{{ config.uiDescription }}</p>
          }
        }
      </header>
    }

    <main class="flex flex-col space-y-4">
      <ng-template cdkPortalOutlet />

      @if (isStringContent) {
        <div data-testid="ui-content" [innerHTML]="config.uiContent"></div>
      }
    </main>

    @if (!config.uiHideFooter) {
      <footer class="flex flex-col-reverse gap-2 sm:flex-row sm:justify-end sm:gap-0 sm:space-x-2">
        @if (config.uiCancelText !== null) {
          <button type="button" data-testid="ui-cancel-button" ui-button uiType="outline" (click)="onCloseClick()">
            @if (config.uiCancelIcon) {
              <ui-icon [uiType]="config.uiCancelIcon" />
            }

            {{ config.uiCancelText ?? 'Cancel' }}
          </button>
        }

        @if (config.uiOkText !== null) {
          <button
            type="button"
            data-testid="ui-ok-button"
            ui-button
            [uiType]="config.uiOkDestructive ? 'destructive' : 'default'"
            [disabled]="config.uiOkDisabled"
            (click)="onOkClick()"
          >
            @if (config.uiOkIcon) {
              <ui-icon [uiType]="config.uiOkIcon" />
            }

            {{ config.uiOkText ?? 'OK' }}
          </button>
        }
      </footer>
    }
  `,
  styles: `
    :host {
      opacity: 1;
      transform: scale(1);
      transition:
        opacity 150ms ease-out,
        transform 150ms ease-out;
    }

    @starting-style {
      :host {
        opacity: 0;
        transform: scale(0.9);
      }
    }

    :host.dialog-leave {
      opacity: 0;
      transform: scale(0.9);
      transition:
        opacity 150ms ease-in,
        transform 150ms ease-in;
    }
  `,
  changeDetection: ChangeDetectionStrategy.OnPush,
  host: {
    '[class]': 'classes()',
    '[style.width]': 'config.uiWidth ? config.uiWidth : null',
    'animate.enter': 'dialog-enter',
    'animate.leave': 'dialog-leave',
  },
  exportAs: 'uiDialog',
})
export class UiDialogComponent<T, U> extends BasePortalOutlet {
  private readonly host = inject(ElementRef<HTMLElement>);
  protected readonly config = inject(UiDialogOptions<T, U>);

  protected readonly classes = computed(() => mergeClasses(dialogVariants(), this.config.uiCustomClasses));
  dialogRef?: UiDialogRef<T>;

  protected readonly isStringContent = typeof this.config.uiContent === 'string';

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
      throw new Error('Attempting to attach modal content after content is already attached');
    }
    return this.portalOutlet()?.attachComponentPortal(portal);
  }

  attachTemplatePortal<C>(portal: TemplatePortal<C>): EmbeddedViewRef<C> {
    if (this.portalOutlet()?.hasAttached()) {
      throw new Error('Attempting to attach modal content after content is already attached');
    }

    return this.portalOutlet()?.attachTemplatePortal(portal);
  }

  onOkClick() {
    this.okTriggered.emit();
  }

  onCloseClick() {
    this.cancelTriggered.emit();
  }
}

@NgModule({
  imports: [UiButtonComponent, UiDialogComponent, OverlayModule, PortalModule],
  providers: [UiDialogService],
})
export class UiDialogModule {}
