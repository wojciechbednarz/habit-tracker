"""Test data used in test methods"""

EXPECTED_RENDERED_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
    <style>
        body { font-family: sans-serif; }
        .habit-card { border: 1px solid #ccc; padding: 10px; margin-bottom: 10px; }
        .status-active { color: green; }
        .status-missed { color: red; }
         </style>
    <title>Weekly Habit Report</title>
</head>
<body>
    <h1>Weekly Habit Report</h1>
    <p>Range: 2026-01-26 00:00:00 to 2026-02-01 23:59:59.999999</p>


    <div class="habit-card">
        <h3>Drink Water</h3>
        <p>Total completions: 5</p>
        <p>Days: ['Mon', 'Tue', 'Wed']</p>
        <p>Status: <span class="status-active"> Active</span></p>
    </div>

    <div class="habit-card">
        <h3>Exercise</h3>
        <p>Total completions: 3</p>
        <p>Days: ['Mon', 'Wed']</p>
        <p>Status: <span class="status-missed"> Missed</span></p>
    </div>

    <div class="habit-card">
        <h3>Read Book</h3>
        <p>Total completions: 0</p>
        <p>Days: []</p>
        <p>Status: <span class="status-missed"> Missed</span></p>
    </div>



</body>
</html>"""
