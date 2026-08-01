import {
  ChangeDetectionStrategy,
  Component,
  input,
  signal,
  ViewEncapsulation,
  output,
  computed,
  viewChild,
  type InputSignal,
  type Signal,
} from '@angular/core';

import type { ClassValue } from 'clsx';
import type { EmblaCarouselType, EmblaEventType, EmblaOptionsType, EmblaPluginType } from 'embla-carousel';
import { EmblaCarouselDirective } from 'embla-carousel-angular';

import { UiButtonComponent } from '../button';
import {
  carouselNextButtonVariants,
  carouselPreviousButtonVariants,
  carouselVariants,
  type UiCarouselControlsVariants,
  type UiCarouselOrientationVariants,
} from './carousel.variants';
import { UiIconComponent } from '../icon';
import { mergeClasses } from '../../utils/merge-classes';

@Component({
  selector: 'ui-carousel',
  imports: [EmblaCarouselDirective, UiButtonComponent, UiIconComponent],
  template: `
    <div class="relative">
      <div
        emblaCarousel
        #emblaRef="emblaCarousel"
        [class]="classes()"
        [options]="options()"
        [plugins]="uiPlugins()"
        [subscribeToEvents]="subscribeToEvents"
        (emblaChange)="onEmblaChange($event, emblaRef.emblaApi!)"
        aria-roledescription="carousel"
        role="region"
        tabindex="0"
      >
        <ng-content />

        @let controls = uiControls();
        @if (controls === 'button') {
          <button
            type="button"
            ui-button
            uiType="outline"
            [class]="prevBtnClasses()"
            [disabled]="!canScrollPrev()"
            (click)="slidePrevious()"
            aria-label="Previous slide"
          >
            <ui-icon uiType="chevron-left" class="size-4" />
          </button>
          <button
            type="button"
            ui-button
            uiType="outline"
            [class]="nextBtnClasses()"
            [disabled]="!canScrollNext()"
            (click)="slideNext()"
            aria-label="Next slide"
          >
            <ui-icon uiType="chevron-right" class="size-4" />
          </button>
        } @else if (controls === 'dot') {
          <div class="mt-2 flex justify-center gap-1">
            @for (dot of dots(); track $index) {
              <button
                type="button"
                [class]="
                  'block size-4 border-0 bg-transparent p-0 ' +
                  ($index === selectedIndex() ? 'cursor-default' : 'cursor-pointer')
                "
                (click)="goTo($index)"
                [attr.aria-current]="$index === selectedIndex() ? 'true' : null"
                [aria-label]="'Go to slide ' + ($index + 1)"
              >
                <ui-icon
                  uiType="circle-small"
                  [uiStrokeWidth]="0"
                  [class]="$index === selectedIndex() ? 'fill-primary' : 'fill-border'"
                />
              </button>
            }
          </div>
        }
      </div>
    </div>
  `,
  changeDetection: ChangeDetectionStrategy.OnPush,
  encapsulation: ViewEncapsulation.None,
  host: {
    '(keydown.arrowleft.prevent)': 'slidePrevious()',
    '(keydown.arrowright.prevent)': 'slideNext()',
  },
})
export class UiCarouselComponent {
  protected readonly emblaRef = viewChild(EmblaCarouselDirective);

  readonly class = input<ClassValue>('');
  readonly uiOptions: InputSignal<EmblaOptionsType> = input<EmblaOptionsType>({ loop: false });
  readonly uiPlugins: InputSignal<EmblaPluginType[]> = input<EmblaPluginType[]>([]);
  readonly uiOrientation = input<UiCarouselOrientationVariants>('horizontal');
  readonly uiControls = input<UiCarouselControlsVariants>('button');
  readonly uiInited = output<EmblaCarouselType>();
  readonly uiSelected = output<void>();

  protected readonly selectedIndex = signal<number>(0);
  protected readonly canScrollPrev = signal<boolean>(false);
  protected readonly canScrollNext = signal<boolean>(false);
  protected readonly scrollSnaps = signal<number[]>([]);
  protected readonly subscribeToEvents: EmblaEventType[] = ['init', 'select', 'reInit'];
  protected readonly options: Signal<EmblaOptionsType> = computed(() => ({
    ...this.uiOptions(),
    axis: this.uiOrientation() === 'horizontal' ? 'x' : 'y',
  }));

  protected readonly dots = computed(() => new Array<string>(this.scrollSnaps().length).fill('.'));

  #index = -1;

  onEmblaChange(type: EmblaEventType, emblaApi: EmblaCarouselType): void {
    if (type === 'init' || type === 'reInit') {
      this.scrollSnaps.set(emblaApi.scrollSnapList());
      this.checkNavigation(emblaApi);
      if (type === 'init') {
        this.uiInited.emit(emblaApi);
      }
      return;
    }

    if (type === 'select' && emblaApi.selectedScrollSnap() !== this.#index) {
      this.checkNavigation(emblaApi);
      this.uiSelected.emit();
    }
  }

  slidePrevious(): void {
    const emblaRef = this.emblaRef();
    if (emblaRef) {
      emblaRef.scrollPrev();
    }
  }

  slideNext(): void {
    const emblaRef = this.emblaRef();
    if (emblaRef) {
      emblaRef.scrollNext();
    }
  }

  goTo(index: number): void {
    const emblaRef = this.emblaRef();
    if (emblaRef) {
      emblaRef.scrollTo(index);
    }
  }

  private checkNavigation(emblaApi: EmblaCarouselType): void {
    this.#index = emblaApi.selectedScrollSnap();
    this.selectedIndex.set(emblaApi.selectedScrollSnap());
    this.canScrollPrev.set(emblaApi.canScrollPrev());
    this.canScrollNext.set(emblaApi.canScrollNext());
  }

  protected readonly classes = computed(() =>
    mergeClasses(carouselVariants({ uiOrientation: this.uiOrientation() }), this.class()),
  );

  protected readonly prevBtnClasses = computed(() =>
    mergeClasses(carouselPreviousButtonVariants({ uiOrientation: this.uiOrientation() })),
  );

  protected readonly nextBtnClasses = computed(() =>
    mergeClasses(carouselNextButtonVariants({ uiOrientation: this.uiOrientation() })),
  );
}
