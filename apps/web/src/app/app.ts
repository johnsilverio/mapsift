import { DecimalPipe } from '@angular/common';
import { Component, inject, signal } from '@angular/core';
import { RouterOutlet } from '@angular/router';

import { UiButtonComponent } from '@mapsift/ui';

import { MAPSIFT_CORE, type Measurement, type Position } from './core/mapsift-core';

const BRASILIA: Position = [-47.8825, -15.7942];
const SAO_PAULO: Position = [-46.6333, -23.5505];

@Component({
  selector: 'app-root',
  imports: [RouterOutlet, DecimalPipe, UiButtonComponent],
  templateUrl: './app.html',
  styleUrl: './app.css',
})
export class App {
  private readonly core = inject(MAPSIFT_CORE);

  protected readonly measurement = signal<Measurement | undefined>(undefined);

  protected measure(): void {
    this.measurement.set(this.core.measureDistance(BRASILIA, SAO_PAULO));
  }
}
