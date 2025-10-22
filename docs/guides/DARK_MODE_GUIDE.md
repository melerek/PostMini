# Dark Mode Guide

PostMini includes a beautiful, professionally-designed dark theme that's easy on the eyes during long coding sessions.

## Features

- **One-Click Toggle**: Switch between light and dark themes instantly
- **Persistent Preference**: Your theme choice is saved and remembered across sessions
- **Professional Design**: Carefully crafted color palette optimized for readability
- **Consistent Experience**: All UI elements follow the dark theme when enabled

## How to Use

### Toggle Theme

1. Look for the theme toggle button in the top-right corner of the toolbar
   - 🌙 Moon icon = Click to switch to **Dark** theme
   - ☀️ Sun icon = Click to switch to **Light** theme

2. Click the button to instantly switch themes

3. Your preference is automatically saved

### Keyboard Shortcut

_(Future enhancement)_: Press `Ctrl+Shift+T` to toggle themes

## Design Philosophy

### Light Theme
- Clean, bright interface
- High contrast for daylight viewing
- Professional blue accents
- Traditional UI aesthetics

### Dark Theme
- Easy on the eyes in low-light environments
- VS Code-inspired color palette
- Reduced eye strain for long sessions
- Modern, professional appearance

## Color Palette (Dark Theme)

### Background Colors
- **Main Background**: `#1e1e1e` (Dark gray)
- **Panel Background**: `#252526` (Slightly lighter gray)
- **Input Background**: `#1e1e1e` (Same as main)
- **Hover Background**: `#3e3e42` (Medium gray)

### Text Colors
- **Primary Text**: `#e0e0e0` (Light gray)
- **Secondary Text**: `#a0a0a0` (Medium gray)
- **Disabled Text**: `#656565` (Dark gray)

### Accent Colors
- **Primary Accent**: `#007acc` (Blue) - Focus states, selections
- **Success**: `#4ec9b0` (Teal)
- **Error**: `#f48771` (Red)
- **Warning**: `#dcdcaa` (Yellow)
- **Info**: `#9cdcfe` (Light blue)

### Borders
- **Default Border**: `#3e3e42` (Medium gray)
- **Focus Border**: `#007acc` (Blue)

## Technical Implementation

### Theme Storage

Theme preferences are stored in: `%APPDATA%/PostMini/settings.json`

Example:
```json
{
  "theme": "dark"
}
```

### Stylesheets

- **Light Theme**: `styles.qss`
- **Dark Theme**: `styles_dark.qss`

Both stylesheets are included with the application and switch automatically.

### Apply at Startup

PostMini loads your saved theme preference automatically when the app starts.

## Troubleshooting

### Theme Not Persisting

If your theme preference isn't saved:
1. Check that the app has write permissions to `%APPDATA%/PostMini/`
2. Verify that `settings.json` exists in the app data directory
3. Check the console for any error messages

### Theme Looks Broken

If the theme doesn't look right:
1. Close and restart the application
2. Try toggling to the other theme and back
3. Check that both `styles.qss` and `styles_dark.qss` exist in the installation directory

### Custom Themes

_(Future enhancement)_: PostMini will support custom theme files. You'll be able to:
- Create your own QSS theme files
- Load custom themes from the settings
- Share themes with the community

## Benefits

### For Developers
- **Reduced Eye Strain**: Perfect for late-night coding sessions
- **Better Focus**: Dark themes help focus on content, not chrome
- **Professional Look**: Matches modern IDEs like VS Code, IntelliJ

### For Teams
- **Consistency**: Everyone can use their preferred theme
- **Accessibility**: Better for users with light sensitivity
- **Modern UX**: Keeps PostMini feeling current and well-maintained

## What's Themed

✅ **All UI Elements Fully Themed:**
- Main window background
- Toolbar and buttons
- Tree widgets (collections view)
- Tab widgets
- Table widgets (headers, parameters, tests)
- Input fields (text, dropdowns)
- Scrollbars
- Dialogs and message boxes
- Context menus
- Splitter handles
- Status indicators

## Comparison with Postman

| Feature | PostMini | Postman |
|---------|----------|---------|
| Dark Theme | ✅ One-click toggle | ✅ Available |
| Theme Persistence | ✅ Automatic | ✅ Automatic |
| Custom Themes | 🚧 Planned | ❌ Not available |
| Theme Quality | ⭐⭐⭐⭐⭐ Professional | ⭐⭐⭐⭐⭐ Professional |

## Future Enhancements

### Coming Soon
- **Theme Variants**: Multiple dark theme options (AMOLED black, Nord, Dracula, etc.)
- **Custom Themes**: Load your own QSS files
- **Theme Editor**: Visual theme customization tool
- **Syntax Highlighting**: Themed JSON/XML syntax highlighting
- **Theme Sharing**: Export/import theme files

### Requested Features
- Auto theme switching based on time of day
- System theme sync (follow OS dark mode)
- Per-collection theme preferences

## Feedback

Love dark mode? Want more themes? Let us know!

We're constantly improving PostMini's design and would love to hear your thoughts on:
- Color palette adjustments
- Additional theme options
- UI contrast improvements
- Accessibility enhancements

---

**Next Steps:**
- Try toggling between themes to see which you prefer
- Check out the [Main Documentation](index.html) for more features
- Explore [Keyboard Shortcuts](../README.md#shortcuts) to work faster

