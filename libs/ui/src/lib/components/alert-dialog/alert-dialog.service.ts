import { type ComponentType, Overlay, OverlayConfig, OverlayRef } from '@angular/cdk/overlay';
import { ComponentPortal, TemplatePortal } from '@angular/cdk/portal';
import { isPlatformBrowser } from '@angular/common';
import {
  inject,
  Injectable,
  InjectionToken,
  Injector,
  PLATFORM_ID,
  TemplateRef,
  type ViewContainerRef,
} from '@angular/core';

import { UiAlertDialogRef } from './alert-dialog-ref';
import { UiAlertDialogComponent, UiAlertDialogOptions } from './alert-dialog.component';

type ContentType<T> = ComponentType<T> | TemplateRef<T> | string | undefined;

export const Z_ALERT_MODAL_DATA = new InjectionToken<unknown>('Z_ALERT_MODAL_DATA');

@Injectable({
  providedIn: 'root',
})
export class UiAlertDialogService {
  private readonly overlay = inject(Overlay);
  private readonly injector = inject(Injector);
  private readonly platformId = inject(PLATFORM_ID);

  create<T>(config: UiAlertDialogOptions<T>): UiAlertDialogRef<T> {
    return this.open<T>(config.uiContent, config);
  }

  confirm<T>(
    config: Omit<UiAlertDialogOptions<T>, 'uiOkText' | 'uiCancelText'> & {
      uiOkText?: string;
      uiCancelText?: string;
    },
  ): UiAlertDialogRef<T> {
    const confirmConfig: UiAlertDialogOptions<T> = {
      ...config,
      uiOkText: config.uiOkText ?? 'Confirm',
      uiCancelText: config.uiCancelText ?? 'Cancel',
      uiOkDestructive: config.uiOkDestructive ?? false,
    };
    return this.create(confirmConfig);
  }

  warning<T>(config: Omit<UiAlertDialogOptions<T>, 'uiOkText'> & { uiOkText?: string }): UiAlertDialogRef<T> {
    const warningConfig: UiAlertDialogOptions<T> = {
      ...config,
      uiOkText: config.uiOkText ?? 'OK',
      uiCancelText: null,
    };
    return this.create(warningConfig);
  }

  info<T>(config: Omit<UiAlertDialogOptions<T>, 'uiOkText'> & { uiOkText?: string }): UiAlertDialogRef<T> {
    const infoConfig: UiAlertDialogOptions<T> = {
      ...config,
      uiOkText: config.uiOkText ?? 'OK',
      uiCancelText: null,
    };
    return this.create(infoConfig);
  }

  private open<T>(componentOrTemplateRef: ContentType<T>, config: UiAlertDialogOptions<T>) {
    const overlayRef = this.createOverlay();

    if (!overlayRef) {
      return new UiAlertDialogRef(
        undefined as unknown as OverlayRef,
        config,
        undefined as unknown as UiAlertDialogComponent<T>,
      );
    }

    const alertDialogContainer = this.attachAlertDialogContainer<T>(overlayRef, config);
    const alertDialogRef = this.attachAlertDialogContent<T>(
      componentOrTemplateRef,
      alertDialogContainer,
      overlayRef,
      config,
    );

    alertDialogContainer.alertDialogRef = alertDialogRef;

    return alertDialogRef;
  }

  private createOverlay(): OverlayRef | undefined {
    if (!isPlatformBrowser(this.platformId)) {
      return undefined;
    }

    const overlayConfig = new OverlayConfig({
      hasBackdrop: true,
      backdropClass: 'cdk-overlay-dark-backdrop',
      positionStrategy: this.overlay.position().global(),
    });

    return this.overlay.create(overlayConfig);
  }

  private attachAlertDialogContainer<T>(overlayRef: OverlayRef, config: UiAlertDialogOptions<T>) {
    const injector = Injector.create({
      parent: this.injector,
      providers: [
        { provide: OverlayRef, useValue: overlayRef },
        { provide: UiAlertDialogOptions, useValue: config },
      ],
    });

    const containerPortal = new ComponentPortal<UiAlertDialogComponent<T>>(
      UiAlertDialogComponent,
      config.uiViewContainerRef,
      injector,
    );

    const containerRef = overlayRef.attach(containerPortal);

    return containerRef.instance;
  }

  private attachAlertDialogContent<T>(
    componentOrTemplateRef: ContentType<T>,
    alertDialogContainer: UiAlertDialogComponent<T>,
    overlayRef: OverlayRef,
    config: UiAlertDialogOptions<T>,
  ) {
    const alertDialogRef = new UiAlertDialogRef<T>(overlayRef, config, alertDialogContainer);

    if (componentOrTemplateRef instanceof TemplateRef) {
      alertDialogContainer.attachTemplatePortal(
        new TemplatePortal<T>(
          componentOrTemplateRef,
          null as unknown as ViewContainerRef,
          {
            alertDialogRef,
          } as T,
        ),
      );
    } else if (componentOrTemplateRef && typeof componentOrTemplateRef !== 'string') {
      const injector = this.createInjector<T>(alertDialogRef, config);
      const contentRef = alertDialogContainer.attachComponentPortal(
        new ComponentPortal(componentOrTemplateRef, config.uiViewContainerRef, injector),
      );
      alertDialogRef.componentInstance = contentRef.instance;
    }

    return alertDialogRef;
  }

  private createInjector<T>(alertDialogRef: UiAlertDialogRef<T>, config: UiAlertDialogOptions<T>) {
    return Injector.create({
      parent: this.injector,
      providers: [
        { provide: UiAlertDialogRef, useValue: alertDialogRef },
        { provide: Z_ALERT_MODAL_DATA, useValue: config.uiData },
      ],
    });
  }
}
