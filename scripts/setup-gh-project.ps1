# One-shot setup of the "habit-tracker — Phase 4 (May–Jun 2026)" GitHub Project (v2 kanban).
#
# Prerequisites:
#   1. gh CLI authenticated: gh auth status
#   2. project scope granted:  gh auth refresh -s project
#
# Idempotent: re-running will report "already exists" but not break anything.

$Owner    = 'wojciechbednarz'
$Repo     = 'habit-tracker'
$Title    = 'habit-tracker - Phase 4 (May-Jun 2026)'

Write-Host "Creating project '$Title' under owner '$Owner'..."
$project = gh project create --owner $Owner --title $Title --format json | ConvertFrom-Json
$ProjectNumber = $project.number
Write-Host "Created project #$ProjectNumber at $($project.url)"

# Add the 10 seeded issues to the project. Do not swallow stderr — fail loudly.
$failures = @()
foreach ($n in 2..11) {
    $issueUrl = "https://github.com/$Owner/$Repo/issues/$n"
    Write-Host "Adding issue #$n to project..."
    gh project item-add $ProjectNumber --owner $Owner --url $issueUrl
    if ($LASTEXITCODE -ne 0) { $failures += $n }
}
if ($failures.Count -gt 0) {
    Write-Host ""
    Write-Host "FAILED to add issues: $($failures -join ', ')" -ForegroundColor Red
    Write-Host "Re-run those individually: gh project item-add $ProjectNumber --owner $Owner --url https://github.com/$Owner/$Repo/issues/<N>"
    exit 1
}

Write-Host ""
Write-Host "Done. Open: $($project.url)"
Write-Host ""
Write-Host "Next: in the web UI, switch the project's view to a Board layout and group by 'Status'."
Write-Host "Add custom Status options if you want: Backlog / This Week / In Progress / Blocked / Done."
