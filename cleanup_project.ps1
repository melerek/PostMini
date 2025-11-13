# PostMini Project Cleanup Script
# Moves development documentation to archive

Write-Host "=== PostMini Project Cleanup ===" -ForegroundColor Cyan
Write-Host ""

# Verify we're in the right directory
if (-not (Test-Path "main.py")) {
    Write-Host "ERROR: Please run this script from the PostMini project root directory" -ForegroundColor Red
    exit 1
}

# Create archive directory if it doesn't exist
$archivePath = "docs\archive"
if (-not (Test-Path $archivePath)) {
    New-Item -ItemType Directory -Path $archivePath -Force | Out-Null
}

# Create release notes directory if it doesn't exist
$releaseNotesPath = "docs\release_notes"
if (-not (Test-Path $releaseNotesPath)) {
    New-Item -ItemType Directory -Path $releaseNotesPath -Force | Out-Null
}

# Implementation notes to archive
$implementationDocs = @(
    "ADDITIONAL_HEIGHT_REDUCTION.md",
    "AUTO_UPDATE_IMPLEMENTATION_SUMMARY.md",
    "AUTO_UPDATE_SETUP.md",
    "COLLAPSIBLE_PANELS_HEIGHT_FIX.md",
    "COMPLETE_SIZING_OPTIMIZATION.md",
    "COMPREHENSIVE_TAB_STATE_MANAGEMENT.md",
    "DESCRIPTION_POPUP_MIGRATION.md",
    "DYNAMIC_TABLE_ROW_MANAGEMENT.md",
    "ENVIRONMENT_IMPORT_EXPORT_IMPLEMENTATION.md",
    "ERROR_HANDLING_IMPROVEMENTS.md",
    "FINAL_ICON_BUTTON_FIX.md",
    "FIX_POSTMAN_FOLDER_IMPORT.md",
    "FOLDER_IMPORT_COMPARISON.md",
    "HEIGHT_CONSTRAINT_FIXES.md",
    "LEFT_PANEL_WIDTH_INCREASE.md",
    "LIGHT_THEME_FIXES_FINAL.md",
    "LIGHT_THEME_READABILITY_IMPROVEMENTS.md",
    "NEW_REQUEST_TAB_REFRESH_FIX.md",
    "PARAMS_HEADERS_TABLE_IMPROVEMENTS.md",
    "REMOVED_AUTO_SORT_FROM_TABLES.md",
    "REQUEST_PANEL_COLLAPSED_HEIGHT_OPTIMIZATION.md",
    "RESPONSE_PANEL_VISIBILITY_IMPROVEMENTS.md",
    "REVERT_THEME_CHANGES.md",
    "SCRIPT_TAB_STATE_FIX.md",
    "SCRIPTING_TEST_GUIDE.md",
    "TAB_STATE_AUDIT_COMPLETE.md",
    "TEST_RESULTS_TAB_MIGRATION.md",
    "THEME_ICON_BAR_FIX.md",
    "THEME_TOGGLE_BUTTON.md",
    "WINDOW_SIZING_FIXES.md"
)

Write-Host "Moving implementation documentation to archive..." -ForegroundColor Yellow
$movedCount = 0
foreach ($doc in $implementationDocs) {
    if (Test-Path $doc) {
        Move-Item -Path $doc -Destination $archivePath -Force
        Write-Host "  Moved $doc" -ForegroundColor Green
        $movedCount++
    }
}
Write-Host "  Moved $movedCount files to archive" -ForegroundColor Cyan
Write-Host ""

# Release notes
$releaseNotes = @(
    "CHECKSUM_FIX_V1.9.0.md",
    "RELEASE_V1.8.6_SUMMARY.md",
    "RELEASE_V1.9.0_COMPLETE.md",
    "RELEASE_V1.9.0_INSTRUCTIONS.md",
    "V1.8.1_HOTFIX_MINI_RACER_DLL.md",
    "V1.8.1_RELEASE_COMPLETE.md",
    "VERSION_FIX_V1.9.0.md",
    "WINDOWS_SMARTSCREEN_FIX.md"
)

Write-Host "Moving release documentation to release_notes..." -ForegroundColor Yellow
$movedCount = 0
foreach ($note in $releaseNotes) {
    if (Test-Path $note) {
        Move-Item -Path $note -Destination $releaseNotesPath -Force
        Write-Host "  Moved $note" -ForegroundColor Green
        $movedCount++
    }
}
Write-Host "  Moved $movedCount files to release_notes" -ForegroundColor Cyan
Write-Host ""

# Remove duplicate files
Write-Host "Removing duplicate build instructions..." -ForegroundColor Yellow
if (Test-Path "BUILD_INSTRUCTIONS.md") {
    Remove-Item "BUILD_INSTRUCTIONS.md" -Force
    Write-Host "  Removed duplicate BUILD_INSTRUCTIONS.md" -ForegroundColor Green
}
if (Test-Path "GIT_RELEASE_INSTRUCTIONS.md") {
    Move-Item "GIT_RELEASE_INSTRUCTIONS.md" -Destination $archivePath -Force
    Write-Host "  Moved GIT_RELEASE_INSTRUCTIONS.md to archive" -ForegroundColor Green
}
Write-Host ""

# Clean build artifacts
Write-Host "Cleaning build artifacts..." -ForegroundColor Yellow
if (Test-Path "build") {
    Remove-Item -Path "build" -Recurse -Force
    Write-Host "  Removed build/" -ForegroundColor Green
}
if (Test-Path "__pycache__") {
    Remove-Item -Path "__pycache__" -Recurse -Force
    Write-Host "  Removed __pycache__/" -ForegroundColor Green
}
Write-Host ""

Write-Host "=== Cleanup Complete ===" -ForegroundColor Green
Write-Host ""
Write-Host "Summary:" -ForegroundColor Cyan
Write-Host "  Implementation docs moved to docs/archive/" -ForegroundColor White
Write-Host "  Release docs moved to docs/release_notes/" -ForegroundColor White
Write-Host "  Duplicate files removed" -ForegroundColor White
Write-Host "  Build artifacts cleaned" -ForegroundColor White
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "  1. Review moved files" -ForegroundColor White
Write-Host "  2. Commit changes" -ForegroundColor White
Write-Host "  3. Test build" -ForegroundColor White
Write-Host ""
