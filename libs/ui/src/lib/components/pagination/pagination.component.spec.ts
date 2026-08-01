import { TestBed } from '@angular/core/testing';

import { UiPaginationComponent } from './pagination.component';

/**
 * Regression: `uiPageIndex` is a `model`, which already emits `uiPageIndexChange`, and the
 * component also declared and emitted that output by hand, so every page change reached the
 * consumer twice. These assert the emission COUNT, because asserting the value passes on the bug.
 */
describe('UiPaginationComponent', () => {
  it('emits one page change per navigation, not one per binding', () => {
    const fixture = TestBed.createComponent(UiPaginationComponent);
    fixture.componentRef.setInput('uiTotal', 5);
    fixture.detectChanges();

    const emitted: number[] = [];
    fixture.componentInstance.uiPageIndex.subscribe((page) => emitted.push(page));

    fixture.componentInstance.goToPage(3);

    expect(emitted).toEqual([3]);
  });

  it('ignores a navigation to the page already shown', () => {
    const fixture = TestBed.createComponent(UiPaginationComponent);
    fixture.componentRef.setInput('uiTotal', 5);
    fixture.detectChanges();

    const emitted: number[] = [];
    fixture.componentInstance.uiPageIndex.subscribe((page) => emitted.push(page));

    fixture.componentInstance.goToPage(1);

    expect(emitted).toEqual([]);
  });

  it('does not navigate while disabled', () => {
    const fixture = TestBed.createComponent(UiPaginationComponent);
    fixture.componentRef.setInput('uiTotal', 5);
    fixture.componentRef.setInput('uiDisabled', true);
    fixture.detectChanges();

    fixture.componentInstance.goToPage(4);

    expect(fixture.componentInstance.uiPageIndex()).toBe(1);
  });
});
