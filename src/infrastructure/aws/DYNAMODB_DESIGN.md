# DynamoDB Single-Table Design for Habit Tracker

This document explains the architecture for integrating DynamoDB into the Habit Tracker project to handle streaks, points, and achievements efficiently.

## 1. Core Concepts: PK, SK, and Single-Table Design

### What is Single-Table Design?
In a traditional SQL database, you create multiple tables (Users, Streaks, Achievements) and "JOIN" them. In DynamoDB, **Joins are not supported**. To get a full picture of a user's progress in one request, we store all related data in **one single table**.

### PK (Partition Key) vs. SK (Sort Key)
*   **PK (Partition Key):** Used to "group" data into a physical bucket. For us, this is the User ID. All data for one user lives together.
*   **SK (Sort Key):** Used to "differentiate" between types of data within that group. It also allows for efficient searching and sorting.

---

## 2. Table Schema (The "Blueprint")

We use a generic `PK` and `SK` to store different entities.

| PK (Partition Key) | SK (Sort Key) | Attributes (Data) | Purpose |
| :--- | :--- | :--- | :--- |
| `USER#{user_id}` | `METADATA` | `total_points`, `username` | User's global stats (Points/Leaderboard) |
| `USER#{user_id}` | `STREAK#{habit_id}` | `current_streak`, `last_completed` | Tracking streaks for a specific habit |
| `USER#{user_id}` | `ACHIEVEMENT#{type}` | `unlocked_at`, `description` | Records of unlocked achievements |

### Why this works:
1.  **Get User Dashboard:** `Query(PK="USER#123")` returns the Metadata, all Streaks, and all Achievements in **one single network call**.
2.  **Update Streak:** `UpdateItem(PK="USER#123", SK="STREAK#gym")` updates only that specific record.

---

## 3. The Leaderboard (GSI)

The **GSI_Leaderboard** is an "index" that looks at your table from a different angle.

*   **How to create it:** You define it in your CloudFormation/Terraform template. You do **not** update it manually.
*   **How it works:** Whenever you update `total_points` in the `METADATA` item, AWS automatically copies that data to the Index.
*   **Query Pattern:** To show the "Top 10 Users", you query the Index by `EntityType=USER` sorted by `total_points` (DESC).

---

## 4. The Event Workflow (Step-by-Step)

### Step 1: Habit Completion
*   **Trigger:** User hits `POST /habits/{id}/complete`.
*   **Action:**
    1.  SQL DB is updated with a new completion record.
    2.  **Crucial Fix:** The router should calculate the actual streak *before* creating the event.
    3.  `HabitCompletedEvent` is dispatched via `BackgroundTasks`.

### Step 2: Handler - `check_streaks`
1.  Receives `HabitCompletedEvent`.
2.  **DynamoDB Action:** Performs an `UpdateItem` on `SK=STREAK#{habit_id}` to increment the streak.
3.  **Logic:** If the new streak hits a milestone (e.g., 7 days), it dispatches an `AchievementUnlockedEvent`.

### Step 3: Handler - `award_points`
1.  Receives `HabitCompletedEvent`.
2.  **Logic:** Calculates points based on the streak (e.g., Base 10 + Multiplier).
3.  **DynamoDB Action:** Performs an `UpdateItem` on `SK=METADATA` to increment `total_points`.
    *   *This update automatically triggers the GSI update for the Leaderboard.*

### Step 4: Handler - `send_notification`
1.  Receives `AchievementUnlockedEvent`.
2.  **Email Action:** Sends the congratulation email via SES.
3.  **DynamoDB Action (New):** Adds a new item with `SK=ACHIEVEMENT#{type}` so it appears in the user's history.

---

## 5. Summary of Key Files

1.  `src/api/v1/routers/habits.py`: Triggers the first event.
2.  `src/core/events/handlers.py`: Contains the logic for updating DynamoDB (currently mocked).
3.  `src/infrastructure/aws/dynamo_client.py` (Recommended): New client to handle the actual AWS SDK calls.
