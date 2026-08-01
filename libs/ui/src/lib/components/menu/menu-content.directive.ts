import { CdkTrapFocus } from '@angular/cdk/a11y';
import { CdkMenu } from '@angular/cdk/menu';
import { computed, Directive, inject, input, type OnInit } from '@angular/core';

import type { ClassValue } from 'clsx';

import { mergeClasses } from '../../utils/merge-classes';

import { menuContentVariants } from './menu.variants';

@Directive({
  selector: '[ui-menu-content]',
  host: {
    '[class]': 'classes()',
    tabindex: '0',
  },
  hostDirectives: [CdkMenu, CdkTrapFocus],
})
export class UiMenuContentDirective implements OnInit {
  private cdkTrapFocus = inject(CdkTrapFocus);
  readonly class = input<ClassValue>('');

  protected readonly classes = computed(() => mergeClasses(menuContentVariants(), this.class()));

  ngOnInit(): void {
    this.cdkTrapFocus.enabled = true;
    this.cdkTrapFocus.autoCapture = true;
  }
}
