import { NgTemplateOutlet } from '@angular/common';
import {
  afterNextRender,
  type AfterViewInit,
  ChangeDetectionStrategy,
  Component,
  computed,
  contentChildren,
  DestroyRef,
  DOCUMENT,
  type ElementRef,
  inject,
  Injector,
  input,
  output,
  runInInjectionContext,
  signal,
  type TemplateRef,
  viewChild,
  ViewEncapsulation,
} from '@angular/core';
import { takeUntilDestroyed, toObservable } from '@angular/core/rxjs-interop';

import clsx from 'clsx';
import { debounceTime, fromEvent, merge, map, distinctUntilChanged } from 'rxjs';
import { twMerge } from 'tailwind-merge';

import { UiButtonComponent } from '../button';
import { UiIconComponent } from '../icon';
import {
  tabButtonVariants,
  tabContainerVariants,
  tabNavVariants,
  type UiTabVariants,
} from './tabs.variants';

export type uiPosition = 'top' | 'bottom' | 'left' | 'right';
export type uiAlign = 'center' | 'start' | 'end';

@Component({
  selector: 'ui-tab',
  imports: [],
  template: `
    <ng-template #content>
      <ng-content />
    </ng-template>
  `,
  changeDetection: ChangeDetectionStrategy.OnPush,
  encapsulation: ViewEncapsulation.None,
})
export class UiTabComponent {
  readonly label = input.required<string>();
  readonly contentTemplate = viewChild.required<TemplateRef<unknown>>('content');
}

@Component({
  selector: 'ui-tab-group',
  imports: [NgTemplateOutlet, UiButtonComponent, UiIconComponent],
  template: `
    @if (navBeforeContent()) {
      <ng-container [ngTemplateOutlet]="navigationBlock" />
    }

    <div class="tab-content flex-1">
      @for (tab of tabs(); track $index; let index = $index) {
        <div
          role="tabpanel"
          [attr.id]="'tabpanel-' + index"
          [attr.aria-labelledby]="'tab-' + index"
          [attr.tabindex]="0"
          [hidden]="activeTabIndex() !== index"
          class="focus-visible:ring-primary/50 outline-none focus-visible:ring-2"
        >
          <ng-container [ngTemplateOutlet]="tab.contentTemplate()" />
        </div>
      }
    </div>

    @if (!navBeforeContent()) {
      <ng-container [ngTemplateOutlet]="navigationBlock" />
    }

    <ng-template #navigationBlock>
      @let horizontal = isHorizontal();

      <div [class]="navGridClasses()">
        @if (showArrow()) {
          @if (horizontal) {
            <button
              type="button"
              [class]="'scroll-btn scroll-left cursor-pointer pr-4 ' + (uiTabsPosition() === 'top' ? 'mb-4' : 'mt-4')"
              (click)="scrollNav('left')"
            >
              <ui-icon uiType="chevron-left" />
            </button>
          } @else {
            <button
              type="button"
              [class]="'scroll-btn scroll-up cursor-pointer pb-4 ' + (uiTabsPosition() === 'left' ? 'mr-4' : 'ml-4')"
              (click)="scrollNav('up')"
            >
              <ui-icon uiType="chevron-up" />
            </button>
          }
        }

        <nav
          [class]="navClasses()"
          #tabNav
          role="tablist"
          [attr.aria-orientation]="horizontal ? 'horizontal' : 'vertical'"
        >
          @for (tab of tabs(); track $index; let index = $index) {
            <button
              type="button"
              ui-button
              uiType="ghost"
              role="tab"
              [attr.id]="'tab-' + index"
              [attr.aria-selected]="activeTabIndex() === index"
              [attr.tabindex]="activeTabIndex() === index ? 0 : -1"
              [attr.aria-controls]="'tabpanel-' + index"
              (click)="setActiveTab(index)"
              [class]="buttonClassesSignal()[index]"
            >
              {{ tab.label() }}
            </button>
          }
        </nav>

        @if (showArrow()) {
          @if (horizontal) {
            <button
              type="button"
              [class]="'scroll-btn scroll-right cursor-pointer pl-4 ' + (uiTabsPosition() === 'top' ? 'mb-4' : 'mt-4')"
              (click)="scrollNav('right')"
            >
              <ui-icon uiType="chevron-right" />
            </button>
          } @else {
            <button
              type="button"
              [class]="'scroll-btn scroll-down cursor-pointer pt-4 ' + (uiTabsPosition() === 'left' ? 'mr-4' : 'ml-4')"
              (click)="scrollNav('down')"
            >
              <ui-icon uiType="chevron-down" />
            </button>
          }
        }
      </div>
    </ng-template>
  `,
  styles: `
    .nav-tab-scroll {
      -webkit-overflow-scrolling: touch;
      scroll-behavior: smooth;
      &::-webkit-scrollbar-thumb {
        background-color: rgba(209, 209, 209, 0.2);
        border-radius: 2px;
      }
      &::-webkit-scrollbar {
        height: 4px;
        width: 4px;
      }
      &::-webkit-scrollbar-button {
        display: none;
      }
    }
  `,
  changeDetection: ChangeDetectionStrategy.OnPush,
  encapsulation: ViewEncapsulation.None,
  host: { '[class]': 'containerClasses()' },
})
export class UiTabGroupComponent implements AfterViewInit {
  private readonly tabComponents = contentChildren(UiTabComponent, { descendants: true });
  private readonly tabsContainer = viewChild.required<ElementRef>('tabNav');
  private readonly destroyRef = inject(DestroyRef);
  private readonly injector = inject(Injector);
  private readonly window = inject(DOCUMENT).defaultView;

  protected readonly tabs = computed(() => this.tabComponents());
  protected readonly activeTabIndex = signal<number>(0);
  protected readonly scrollPresent = signal<boolean>(false);

  protected readonly uiTabChange = output<{
    index: number;
    label: string;
    tab: UiTabComponent;
  }>();

  protected readonly uiDeselect = output<{
    index: number;
    label: string;
    tab: UiTabComponent;
  }>();

  readonly uiTabsPosition = input<UiTabVariants['uiPosition']>('top');
  readonly uiActivePosition = input<UiTabVariants['uiActivePosition']>('bottom');
  readonly uiShowArrow = input(true);
  readonly uiScrollAmount = input(100);
  readonly uiAlignTabs = input<uiAlign>('start');
  // Preserve consumer classes on host
  readonly class = input<string>('');

  protected readonly showArrow = computed(() => this.uiShowArrow() && this.scrollPresent());

  ngAfterViewInit(): void {
    // default tab selection
    if (this.tabs().length) {
      this.setActiveTab(0);
    }

    runInInjectionContext(this.injector, () => {
      const observeInputs$ = merge(
        toObservable(this.uiShowArrow),
        toObservable(this.tabs),
        toObservable(this.uiTabsPosition),
      );

      // Re-observe whenever #tabNav reference changes (e.g., when placement toggles)
      let observedEl: HTMLElement | null = null;
      const tabNavEl$ = toObservable(this.tabsContainer).pipe(
        map(ref => ref.nativeElement as HTMLElement),
        distinctUntilChanged(),
      );

      afterNextRender(() => {
        // SSR/browser guard
        if (!this.window || typeof ResizeObserver === 'undefined') {
          return;
        }

        const resizeObserver = new ResizeObserver(() => this.setScrollState());

        tabNavEl$.pipe(takeUntilDestroyed(this.destroyRef)).subscribe(el => {
          if (observedEl) {
            resizeObserver.unobserve(observedEl);
          }
          observedEl = el;
          resizeObserver.observe(el);
          this.setScrollState();
        });

        merge(observeInputs$, fromEvent(this.window, 'resize'))
          .pipe(debounceTime(10), takeUntilDestroyed(this.destroyRef))
          .subscribe(() => this.setScrollState());

        this.destroyRef.onDestroy(() => resizeObserver.disconnect());
      });
    });
  }

  private setScrollState(): void {
    if (this.hasScroll() !== this.scrollPresent()) {
      this.scrollPresent.set(this.hasScroll());
    }
  }

  private hasScroll(): boolean {
    const navElement: HTMLElement = this.tabsContainer().nativeElement;
    if (this.uiShowArrow()) {
      return navElement.scrollWidth > navElement.clientWidth || navElement.scrollHeight > navElement.clientHeight;
    }
    return false;
  }

  protected setActiveTab(index: number) {
    const currentTab = this.tabs()[this.activeTabIndex()];
    if (index !== this.activeTabIndex()) {
      this.uiDeselect.emit({
        index: this.activeTabIndex(),
        label: currentTab.label(),
        tab: currentTab,
      });
    }

    this.activeTabIndex.set(index);
    const activeTabComponent = this.tabs()[index];
    if (activeTabComponent) {
      this.uiTabChange.emit({
        index,
        label: activeTabComponent.label(),
        tab: activeTabComponent,
      });
    }
  }

  protected readonly navBeforeContent = computed(() => {
    const position = this.uiTabsPosition();
    return position === 'top' || position === 'left';
  });

  protected readonly isHorizontal = computed(() => {
    const position = this.uiTabsPosition();
    return position === 'top' || position === 'bottom';
  });

  protected readonly navGridClasses = computed(() => {
    const gridLayout = this.isHorizontal() ? 'grid-cols-[25px_1fr_25px]' : 'grid-rows-[25px_1fr_25px]';
    if (this.showArrow()) {
      return twMerge(clsx('grid', gridLayout));
    }
    return 'grid';
  });

  protected readonly containerClasses = computed(() =>
    twMerge(tabContainerVariants({ uiPosition: this.uiTabsPosition() }), this.class()),
  );

  protected readonly navClasses = computed(() =>
    tabNavVariants({ uiPosition: this.uiTabsPosition(), uiAlignTabs: this.showArrow() ? 'start' : this.uiAlignTabs() }),
  );

  protected readonly buttonClassesSignal = computed(() => {
    const activeIndex = this.activeTabIndex();
    const position = this.uiActivePosition();
    return this.tabs().map((_, index) => {
      const isActive = activeIndex === index;
      return tabButtonVariants({ uiActivePosition: position, isActive });
    });
  });

  protected scrollNav(direction: 'left' | 'right' | 'up' | 'down') {
    const container = this.tabsContainer().nativeElement;
    const scrollAmount = this.uiScrollAmount();
    if (direction === 'left') {
      container.scrollLeft -= scrollAmount;
    } else if (direction === 'right') {
      container.scrollLeft += scrollAmount;
    } else if (direction === 'up') {
      container.scrollTop -= scrollAmount;
    } else if (direction === 'down') {
      container.scrollTop += scrollAmount;
    }
  }

  selectTabByIndex(index: number): void {
    if (index >= 0 && index < this.tabs().length) {
      this.setActiveTab(index);
    } else {
      console.warn(`Index ${index} outside the range of available tabs.`);
    }
  }
}
