Can src/infrastructure/aws/aws_helper.py work within Lambda execution context?

Status: [x] Done

🔴 No. `get_aws_session` passes `AWS_ACCESS_KEY_ID` + `AWS_SECRET_ACCESS_KEY` from settings but drops `AWS_SESSION_TOKEN` — Lambda exec-role temp creds need the token, so AWS calls fail.

Fix (Option A): if `os.getenv("AWS_LAMBDA_FUNCTION_NAME")`, return `Session(region_name=self.region)` with no keys → boto3 default chain picks up all three exec-role env vars including the session token.

Decision A still holds — defect is localized, not architectural.

---

Does FastAPI BackgroundTasks (`habits.py:156`) work under Mangum + Lambda?

Status: [x] Done

🟢 Yes. Starlette `await`s background tasks inside the response coroutine, so they complete before Mangum returns to Lambda — tasks aren't dropped. The plan's "tasks may be dropped" framing was the wrong failure mode.

Real cost: tasks become effectively foreground in Lambda (no socket → client waits for tasks before getting the response). For `complete_habit`: ~150-400ms typical added latency, ~600-1500ms on milestones (SES send dominates). Acceptable for v1.

Decision: Option (a) — keep `BackgroundTasks` pattern. No code change. Preserves async-after-response benefit if we ever migrate off Lambda. SQS-decoupled dispatch is a Week 12+ polish path.


Are there SQL patterns in src/repository/ that block DDB migration?

Status: [x] Done

🟢 No. Audit found one aggregation (`get_at_risk_habits`) — denormalizable per plan §5. All other queries map cleanly: GetItem / Query / single-table flattening. Max join is 2 entities.

Two additions for SAM template: (1) GSIs on User.email and User.username (auth-path), (2) delete `execute_query` escape hatch — only callers pass "DELETE FROM habits", migrate to `delete_all`.


What does HabitCompletedEvent actually trigger? Is BackgroundTasks risk real?

Status: [x] Done

🟢 No-op for v1. One handler fires on every event (`check_streaks`):
1 PG SELECT (~30-80ms in Lambda+Neon). Milestone path adds 1 PG SELECT + 1 SES call (~320-900ms). All under acceptable UX threshold. (The `award_points` handler referenced in earlier drafts has since been removed — points are computed on the read path via `src/core/streak_service.compute_completion_points`, not persisted.)

Confirms slot 2 verdict — `BackgroundTasks` pattern stays. SES is the only real latency offender; SQS-decouple as a Week 12+ polish if more email-sending features land.


Is Anthropic Claude available in eu-central-1 / eu-west-1 on Bedrock?

Status: [x] Done

🟢 Yes. Console check confirms Anthropic Claude models (4.x Sonnet/Haiku/Opus + 3.x Haiku) available in EU regions. No need for us-east-1 cross-region invocation, Decision D regional reversal trigger NOT fired.

Note: original plan §15 targeted `claude-3-5-sonnet-20241022-v2:0`, but Sonnet 4.5/4.6 are now available — free upgrade for Week 11 build, same `bedrock-runtime:InvokeModel` shape.


AWS RDS Free Tier?
- i should be still in the 12 month free tier and RDS usage should be free
