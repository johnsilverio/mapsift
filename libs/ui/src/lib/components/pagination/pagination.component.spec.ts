import { TestBed } from '@angular/core/testing';

import { UiPaginationComponent } from './pagination.component';

/**
 * A regression test for a defect this library shipped with: `uiPageIndex` is a `model`, so
 * Angular already exposes `uiPageIndexChange` and emits it on every `set`, and the component
 * also declared that output explicitly and emitted it by hand. The v22 compiler rejects the
 * duplicate outright (NG1054), but the interesting half is what it did before that: every page
 * change reached the consumer twice, so anything counting changes or fetching per change did
 * the work twice and nothing in the type system objected.
 *
 * Asserting the emission count, rather than the value, is the point. A test that only checked
 * the value would have passed happily against the bug.
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
