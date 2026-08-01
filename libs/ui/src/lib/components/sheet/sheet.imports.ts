import { OverlayModule } from '@angular/cdk/overlay';
import { PortalModule } from '@angular/cdk/portal';

import { UiSheetComponent } from './sheet.component';

export const UiSheetImports = [UiSheetComponent, OverlayModule, PortalModule] as const;
