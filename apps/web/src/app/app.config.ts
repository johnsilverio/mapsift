import { ApplicationConfig, provideBrowserGlobalErrorListeners } from '@angular/core';
import { provideRouter } from '@angular/router';

import { routes } from './app.routes';
import { MAPSIFT_CORE } from './core/mapsift-core';
import { wasmMapsiftCore } from './core/wasm-mapsift-core';

export const appConfig: ApplicationConfig = {
  providers: [provideBrowserGlobalErrorListeners(), provideRouter(routes),
    { provide: MAPSIFT_CORE, useValue: wasmMapsiftCore },
  ],
};
