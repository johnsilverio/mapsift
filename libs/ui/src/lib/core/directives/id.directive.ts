import { Directive, inject, Injectable, input, computed } from '@angular/core';

@Injectable({ providedIn: 'root' })
class UiIdInternalService {
  private counter = 0;
  generate(prefix: string) {
    return `${prefix}-${++this.counter}`;
  }
}

@Directive({
  selector: '[uiId]',
  exportAs: 'uiId',
})
export class UiIdDirective {
  private idService = inject(UiIdInternalService);

  readonly uiId = input('ssr');

  readonly id = computed(() => this.idService.generate(this.uiId()));
}
