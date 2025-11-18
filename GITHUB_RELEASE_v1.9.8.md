## ✨ New Features

### 🔮 Variable Autocomplete System
- **NEW** - Smart autocomplete for variables when typing in any input field
- **Trigger Characters** - Autocomplete appears when typing `{{` or `:` (for path parameters)
- **All Scopes Supported** - Shows variables from environment, collection, extracted, and dynamic scopes
- **Visual Design** - Modern dropdown with variable name, color-coded scope badge, and value preview
- **Scope Color Coding** - Blue (environment), Purple (collection), Green (extracted), Orange (dynamic)
- **Keyboard Navigation** - Tab/Down for next, Shift+Tab/Up for previous, Enter to select, Escape to close
- **Mouse Support** - Click any suggestion to instantly insert it
- **Live Filtering** - Type after `{{` to filter variables by name or value in real-time
- **Smart Insertion** - Automatically adds closing `}}` for variables, correct syntax for path parameters
- **Universal Support** - Works in URL input, request body, params table, and headers table
- **Variable Tooltips** - Hover over any variable to see its resolved value with copy-to-clipboard button
- **Theme Integration** - Fully styled for both light and dark themes

## 🎨 UI/UX Enhancements
- **Autocomplete UX** - Professional dropdown with smooth keyboard/mouse navigation
- **Variable Tooltips** - Rich tooltips show variable values with copy button when hovering
- **Tooltip Persistence** - Tooltips stay visible when moving mouse to them for easy interaction
- **Smart Positioning** - Autocomplete and tooltips position themselves intelligently to stay on screen
- **Seamless Integration** - Autocomplete blends naturally with existing variable highlighting system

## 🔧 Technical Improvements
- **New Widget Components**: `VariableAutocompleteWidget`, `VariableAutocompleteItem`, `AutocompleteTextEdit`, `VariableTooltipWidget`
- **Enhanced HighlightedLineEdit** - Extended with autocomplete for URL field and table cells
- **Theme System** - Autocomplete fully integrated with light/dark theme switching

## 📦 Installation & Checksums

Download: [PostMini_Setup_v1.9.8.exe](https://github.com/melerek/PostMini/releases/download/v1.9.8/PostMini_Setup_v1.9.8.exe)

**Checksums (SHA256):**
- **Executable**: `57F3AAAD23CA524F8F348064F599C5C0EAA7859F4596C205C753ACDE544CEC99`
- **Installer**: `BCD72B3DAEDD204F0AB2214323061D9FE66E2D29E1FAA85507BFD75CFD88A482`

**Full Changelog**: https://github.com/melerek/PostMini/blob/main/CHANGELOG.md
