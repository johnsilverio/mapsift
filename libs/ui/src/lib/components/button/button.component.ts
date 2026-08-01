import {
  afterNextRender,
  ChangeDetectionStrategy,
  Component,
  computed,
  type OnDestroy,
  ElementRef,
  inject,
  input,
  signal,
  ViewEncapsulation,
  booleanAttribute,
} from '@angular/core';

import type { ClassValue } from 'clsx';

import { mergeClasses } from '../../utils/merge-classes';

import {
  buttonVariants,
  type UiButtonShapeVariants,
  type UiButtonSizeVariants,
  type UiButtonTypeVariants,
} from './button.variants';
import { UiIconComponent } from '../icon/icon.component';

@Component({
  selector: 'ui-button, button[ui-button], a[ui-button]',
  imports: [UiIconComponent],
  template: `
    @if (uiLoading()) {
      <ui-icon uiType="loader-circle" class="animate-spin duration-2000" />
    }
    <ng-content />
  `,
  changeDetection: ChangeDetectionStrategy.OnPush,
  encapsulation: ViewEncapsulation.None,
  host: {
    '[class]': 'classes()',
    '[attr.data-icon-only]': 'iconOnly() || null',
    '[attr.data-disabled]': 'isNotInsideOfButtonOrLink() && uiDisabled() || null',
    '[attr.aria-disabled]': 'isNotInsideOfButtonOrLink() && uiDisabled() || null',
    '[attr.disabled]': 'isNotInsideOfButtonOrLink() && uiDisabled() ? "" : null',
    '[attr.role]': 'isNotInsideOfButtonOrLink() ? "button" : null',
    '[attr.tabindex]': 'isNotInsideOfButtonOrLink() ? "0" : null',
  },
  exportAs: 'uiButton',
})
export class UiButtonComponent implements OnDestroy {
  private readonly elementRef = inject(ElementRef<HTMLElement>);

  readonly uiType = input<UiButtonTypeVariants>('default');
  readonly uiSize = input<UiButtonSizeVariants>('default');
  readonly uiShape = input<UiButtonShapeVariants>('default');
  readonly class = input<ClassValue>('');
  readonly uiFull = input(false, { transform: booleanAttribute });
  readonly uiLoading = input(false, { transform: booleanAttribute });
  readonly uiDisabled = input(false, { transform: booleanAttribute });

  private readonly iconOnlyState = signal(false);
  readonly iconOnly = this.iconOnlyState.asReadonly();

  private _mutationObserver: MutationObserver | null = null;

  constructor() {
    afterNextRender(() => {
      if (typeof window === 'undefined' || typeof MutationObserver === 'undefined') {
        return;
      }

      const check = () => {
        const el = this.elementRef.nativeElement;
        const hasIcon = el.querySelector('ui-icon, [ui-icon]') !== null;
        const children = Array.from<Node>(el.childNodes);
        const hasText = children.some(node => {
          if (node.nodeType === 3) {
            return node.textContent?.trim() !== '';
          }
          if (node.nodeType === 1) {
            const element = node as HTMLElement;
            if (element.matches('ui-icon, [ui-icon]')) {
              return false;
            }
            return element.textContent?.trim() !== '';
          }
          return false;
        });

        this.iconOnlyState.set(hasIcon && !hasText);
      };

      check();
      this._mutationObserver = new MutationObserver(check);
      this._mutationObserver.observe(this.elementRef.nativeElement, {
        childList: true,
        characterData: true,
        subtree: true,
      });
    });
  }

  ngOnDestroy(): void {
    if (this._mutationObserver) {
      this._mutationObserver.disconnect();
      this._mutationObserver = null;
    }
  }

  protected readonly classes = computed(() =>
    mergeClasses(
      buttonVariants({
        uiType: this.uiType(),
        uiSize: this.uiSize(),
        uiShape: this.uiShape(),
        uiFull: this.uiFull(),
        uiLoading: this.uiLoading(),
        uiDisabled: this.uiDisabled(),
      }),
      this.class(),
    ),
  );

  protected readonly isNotInsideOfButtonOrLink = computed(() => {
    // Evaluated once; assumes component parent doesn't change after mount
    const uiButtonElement = this.elementRef.nativeElement;
    if (uiButtonElement.parentElement) {
      const { tagName } = uiButtonElement.parentElement;
      return tagName !== 'BUTTON' && tagName !== 'A';
    }
    return true;
  });
}
