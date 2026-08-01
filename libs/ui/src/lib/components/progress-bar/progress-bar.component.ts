import {
  booleanAttribute,
  ChangeDetectionStrategy,
  Component,
  computed,
  input,
  ViewEncapsulation,
} from '@angular/core';

import type { ClassValue } from 'clsx';

import { mergeClasses } from '../../utils/merge-classes';

import {
  containerProgressBarVariants,
  progressBarVariants,
  type UiProgressBarShapeVariants,
  type UiProgressBarSizeVariants,
  type UiProgressBarTypeVariants,
} from './progress-bar.variants';

@Component({
  selector: 'ui-progress-bar',
  template: `
    @if (uiIndeterminate()) {
      <div [class]="classes()">
        <div [class]="barClasses()"></div>
      </div>
    } @else {
      <div [class]="classes()">
        <div [style.width.%]="correctedProgress()" [class]="barClasses()" id="bar"></div>
      </div>
    }
  `,
  styles: `
    @keyframes indeterminate {
      0% {
        left: -0%;
        width: 30%;
      }
      50% {
        left: 50%;
        width: 30%;
      }
      100% {
        left: 100%;
        width: 0;
      }
    }
  `,
  changeDetection: ChangeDetectionStrategy.OnPush,
  encapsulation: ViewEncapsulation.None,
  host: {
    class: 'w-full',
  },
})
export class UiProgressBarComponent {
  readonly uiType = input<UiProgressBarTypeVariants>('default');
  readonly uiSize = input<UiProgressBarSizeVariants>('default');
  readonly uiShape = input<UiProgressBarShapeVariants>('default');
  readonly uiIndeterminate = input(false, { transform: booleanAttribute });
  readonly class = input<ClassValue>('');
  readonly barClass = input<ClassValue>('');
  readonly progress = input(0);

  readonly correctedProgress = computed(() => {
    if (this.progress() > 100) {
      return 100;
    } else if (this.progress() < 0) {
      return 0;
    }
    return this.progress();
  });

  protected readonly classes = computed(() =>
    mergeClasses(
      containerProgressBarVariants({
        uiIndeterminate: this.uiIndeterminate(),
        uiType: this.uiType(),
        uiSize: this.uiSize(),
        uiShape: this.uiShape(),
      }),
      this.class(),
    ),
  );

  protected readonly barClasses = computed(() =>
    mergeClasses(
      progressBarVariants({ uiIndeterminate: this.uiIndeterminate(), uiType: this.uiType(), uiShape: this.uiShape() }),
      this.barClass(),
    ),
  );
}
