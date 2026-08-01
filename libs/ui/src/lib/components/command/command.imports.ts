import { UiCommandDividerComponent } from './command-divider.component';
import { UiCommandEmptyComponent } from './command-empty.component';
import { UiCommandInputComponent } from './command-input.component';
import { UiCommandListComponent } from './command-list.component';
import { UiCommandOptionGroupComponent } from './command-option-group.component';
import { UiCommandOptionComponent } from './command-option.component';
import { UiCommandComponent } from './command.component';

export const UiCommandImports = [
  UiCommandComponent,
  UiCommandInputComponent,
  UiCommandListComponent,
  UiCommandEmptyComponent,
  UiCommandOptionComponent,
  UiCommandOptionGroupComponent,
  UiCommandDividerComponent,
] as const;
