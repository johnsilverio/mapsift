import { TestBed } from '@angular/core/testing';

import { App } from './app';
import { MAPSIFT_CORE, type MapsiftCore } from './core/mapsift-core';

const fakeCore: MapsiftCore = {
  measureDistance: () => ({
    value: 868548,
    unit: 'm',
    frame: 'geodesic:SIRGAS2000',
    authority: 'client-preview',
  }),
};

describe('App', () => {
  beforeEach(() =>
    TestBed.configureTestingModule({
      providers: [{ provide: MAPSIFT_CORE, useValue: fakeCore }],
    }),
  );

  it('renders nothing until a measurement is asked for', () => {
    const fixture = TestBed.createComponent(App);
    fixture.detectChanges();

    expect(fixture.nativeElement.textContent).not.toContain('client-preview');
  });

  it('shows the measurement with the frame and authority that produced it', () => {
    const fixture = TestBed.createComponent(App);
    fixture.detectChanges();

    fixture.nativeElement.querySelector('button').click();
    fixture.detectChanges();

    expect(fixture.nativeElement.textContent).toContain('868,548');
    expect(fixture.nativeElement.textContent).toContain('client-preview');
  });
});
