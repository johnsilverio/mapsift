import { OverlayModule } from '@angular/cdk/overlay';

import { UiTooltipComponent, UiTooltipDirective } from './tooltip';

export const UiTooltipImports = [UiTooltipComponent, UiTooltipDirective, OverlayModule] as const;
