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
  output,
  signal,
  type TemplateRef,
  type Type,
  viewChild,
  type ViewContainerRef,
} from '@angular/core';

import { mergeClasses, noopFn } from '../../utils/merge-classes';

import type { UiSheetRef } from './sheet-ref';
import { sheetVariants, type UiSheetVariants } from './sheet.variants';
import { UiButtonComponent } from '../button/button.component';
import { UiIconComponent } from '../icon/icon.component';
import type { UiIcon } from '../icon/icons';

export type OnClickCallback<T> = (instance: T) => false | void | object;
export class UiSheetOptions<T, U> {
  uiCancelIcon?: UiIcon;
  uiCancelText?: string | null;
  uiClosable?: boolean;
  uiContent?: string | TemplateRef<T> | Type<T>;
  uiCustomClasses?: string;
  uiData?: U;
  uiDescription?: string;
  uiHeight?: string;
  uiHideFooter?: boolean;
  uiMaskClosable?: boolean;
  uiOkDestructive?: boolean;
  uiOkDisabled?: boolean;
  uiOkIcon?: UiIcon;
  uiOkText?: string | null;
  uiOnCancel?: EventEmitter<T> | OnClickCallback<T> = noopFn;
  uiOnOk?: EventEmitter<T> | OnClickCallback<T> = noopFn;
  uiSide?: UiSheetVariants['uiSide'] = 'left';
  uiSize?: UiSheetVariants['uiSize'] = 'default';
  uiTitle?: string | TemplateRef<T>;
  uiViewContainerRef?: ViewContainerRef;
  uiWidth?: string;
}

@Component({
  selector: 'ui-sheet',
  imports: [OverlayModule, PortalModule, UiButtonComponent, UiIconComponent],
  template: `
    @if (config.uiClosable || config.uiClosable === undefined) {
      <button
        type="button"
        data-testid="ui-close-header-button"
        ui-button
        uiType="ghost"
        uiSize="sm"
        class="absolute top-1 right-1 cursor-pointer"
        (click)="onCloseClick()"
      >
        <ui-icon uiType="x" />
      </button>
    }

    @if (config.uiTitle || config.uiDescription) {
      <header data-slot="sheet-header" class="flex flex-col gap-1.5 p-4">
        @if (config.uiTitle) {
          <h4 data-testid="ui-title" data-slot="sheet-title" class="text-lg leading-none font-semibold tracking-tight">
            {{ config.uiTitle }}
          </h4>

          @if (config.uiDescription) {
            <p data-testid="ui-description" data-slot="sheet-description" class="text-muted-foreground text-sm">
              {{ config.uiDescription }}
            </p>
          }
        }
      </header>
    }

    <main class="flex w-full flex-col space-y-4">
      <ng-template cdkPortalOutlet />

      @if (isStringContent) {
        <div data-testid="ui-content" data-slot="sheet-content" [innerHTML]="config.uiContent"></div>
      }
    </main>

    @if (!config.uiHideFooter) {
      <footer data-slot="sheet-footer" class="mt-auto flex flex-col gap-2 p-4">
        @if (config.uiOkText !== null) {
          <button
            type="button"
            data-testid="ui-ok-button"
            class="cursor-pointer"
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

        @if (config.uiCancelText !== null) {
          <button
            type="button"
            data-testid="ui-cancel-button"
            class="cursor-pointer"
            ui-button
            uiType="outline"
            (click)="onCloseClick()"
          >
            @if (config.uiCancelIcon) {
              <ui-icon [uiType]="config.uiCancelIcon" />
            }

            {{ config.uiCancelText ?? 'Cancel' }}
          </button>
        }
      </footer>
    }
  `,
  changeDetection: ChangeDetectionStrategy.OnPush,
  host: {
    'data-slot': 'sheet',
    '[class]': 'classes()',
    '[attr.data-state]': 'state()',
    '[style.width]': 'config.uiWidth ? config.uiWidth + " !important" : null',
    '[style.height]': 'config.uiHeight ? config.uiHeight + " !important" : null',
  },
  exportAs: 'uiSheet',
})
export class UiSheetComponent<T, U> extends BasePortalOutlet {
  private readonly host = inject(ElementRef<HTMLElement>);
  protected readonly config = inject(UiSheetOptions<T, U>);

  protected readonly classes = computed(() => {
    const uiSize = this.config.uiWidth || this.config.uiHeight ? 'custom' : this.config.uiSize;

    return mergeClasses(
      sheetVariants({
        uiSide: this.config.uiSide,
        uiSize,
      }),
      this.config.uiCustomClasses,
    );
  });

  sheetRef?: UiSheetRef<T>;

  protected readonly isStringContent = typeof this.config.uiContent === 'string';

  readonly portalOutlet = viewChild.required(CdkPortalOutlet);

  readonly okTriggered = output<void>();
  readonly cancelTriggered = output<void>();
  readonly state = signal<'closed' | 'open'>('closed');

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
