# SQS → Lambda Event-Source Migration Plan

**GH Issue:** #36
**Status:** Plan only — no implementation yet.
**IaC tool:** AWS SAM
**Existing SQS stack:** `src/infrastructure/aws/data/sqs_queue.yml` (queue only, no DLQ, no event-source mapping)
**Entry point today:** `src/infrastructure/aws/lambda_entry.py` (Mangum — HTTP events; **wrong shape for SQS**).

---

## 1. What changes and why

| Area | Now | After migration |
|------|-----|-----------------|
| Consumer | `worker.py` long-poll loop (manually calls `receive_message`, `delete_message`) | Lambda handler triggered by SQS event-source mapping — no manual polling, no manual delete |
| Entry point | `lambda_entry.py` → Mangum (HTTP only) | New `lambda_sqs_worker.py` — standalone handler, no web layer |
| ACK | `delete_message()` called inside `process_message` AFTER SES send | Removed — Lambda event-source mapping ACKs the batch on clean return; failures returned via `batchItemFailures` |
| Idempotency | None — S3 upload + SES send are blind repeats | `s3.head_object(Key=s3_key)` before generate+email; skip if key exists |
| Partial failure | Full batch retried on any error | `ReportBatchItemFailures`: only the failed message IDs are retried, not the whole batch |
| DLQ | Not configured — infinite redelivery bug | DLQ added to the SQS queue; messages land there after `maxReceiveCount` |
| Sync blocking calls | `PDFGenerator` (sync), `render_html_report` (sync), `create_report` (sync) | Wrapped in `asyncio.to_thread()` — prevents event-loop blocking inside Lambda |

---

## 2. Lambda packaging decision

**Not Mangum.** Mangum wraps ASGI (HTTP events) — it can't handle `event["Records"]` SQS shape.

New file: `src/infrastructure/aws/lambda_sqs_worker.py`
- Imports only what it needs: `parse_message`, `AppContainer`, `ReportService`, `PDFGenerator`, `S3Client`, `SESClient`.
- No FastAPI, no Mangum, no web layer.
- Services live at their current paths (`src/infrastructure/pdf/`, `src/core/`) — **no duplication needed**; same package tree, Lambda layer or zip includes `src/`.

---

## 3. Handler shape (pseudocode — not implementation)

```
handler(event, context):
    container = AppContainer()
    failures = []

    for record in event["Records"]:
        message_id = record["messageId"]
        try:
            body = parse_message(record["body"])
            user_id, report = body.user_id, body.report

            # Idempotency gate — skip if report already on S3
            s3_key = f"reports/{user_id}/weekly_w{report.week_number}.pdf"
            if s3_object_exists(container.s3_client, s3_key):
                continue   # already processed; safe to ack

            # Sync calls go in asyncio.to_thread()
            stats = await container.report_service.calculate_weekly_stats(...)
            html  = await asyncio.to_thread(container.report_service.render_html_report, stats)
            pdf   = await asyncio.to_thread(PDFGenerator.generate, html)

            await container.s3_client.upload(s3_key, pdf)
            await container.ses_client.send(user_id, s3_key)
            # NO delete_message here — event-source mapping ACKs on clean return

        except Exception:
            failures.append({"itemIdentifier": message_id})

    return {"batchItemFailures": failures}
```

**Why this order:** S3 upload before SES send. A crash after upload but before SES = retry → idempotency gate blocks duplicate upload → SES fires once. Crash after SES = already delivered, but retry is caught by idempotency gate (key exists) → skipped. Safest achievable at-least-once.

---

## 4. IaC additions (SAM)

All in `sqs_queue.yml` or a new `lambda_sqs.yml` — **not yet written**.

### 4a. DLQ (add to existing queue template)

```yaml
HabitReportDLQ:
  Type: AWS::SQS::Queue
  Properties:
    QueueName: habit-reports-dlq
    MessageRetentionPeriod: 1209600  # 14 days

HabitReportQueue:
  # existing properties +
  RedrivePolicy:
    deadLetterTargetArn: !GetAtt HabitReportDLQ.Arn
    maxReceiveCount: 3   # 3 delivery attempts → DLQ on 4th
```

**`maxReceiveCount: 3` rationale:** enough retries for transient errors (throttle, network); low enough to not spam. Tune up if PDF generation is flaky.

**`VisibilityTimeout`:** must be ≥ Lambda timeout. Current = 30s. Lambda timeout for PDF+email work should be 60-120s — **raise `VisibilityTimeout` to 120s** before wiring event-source mapping or messages will become visible mid-execution and be re-delivered.

### 4b. Lambda function (SAM)

```yaml
ReportWorkerFunction:
  Type: AWS::Serverless::Function
  Properties:
    Handler: src/infrastructure/aws/lambda_sqs_worker.handler
    Runtime: python3.13
    Timeout: 120
    MemorySize: 512    # PDFGenerator is CPU+memory-bound
    Events:
      SQSTrigger:
        Type: SQS
        Properties:
          Queue: !GetAtt HabitReportQueue.Arn
          BatchSize: 1        # start with 1 — easier to reason about failures
          FunctionResponseTypes:
            - ReportBatchItemFailures
    Policies:
      - SQSSendMessagePolicy:
          QueueName: !GetAtt HabitReportQueue.QueueName
      - S3CrudPolicy:
          BucketName: !Ref ReportsBucket
      - SESEmailPolicy: ...
      - CloudWatchPutMetricPolicy: {}
```

**`BatchSize: 1` rationale:** for now. With batch > 1, a partial failure means only the failed message IDs retry — but `batchItemFailures` is already wired. Raise to 5-10 later once the handler is proven. Start simple.

---

## 5. Open risks / decisions before implementation

| Risk | Decision needed |
|------|----------------|
| `VisibilityTimeout` (30s) < Lambda timeout (120s) | Raise to 120s in `sqs_queue.yml` before event-source mapping |
| `AppContainer` initialisation — does it work outside FastAPI DI context? | Verify; may need a lightweight factory for Lambda cold-start |
| asyncio entrypoint — Lambda calls `handler(event, context)` synchronously | Wrap with `asyncio.run(async_handler(event, context))` at module level |
| `delete_message` still present in `process_message` | Remove before reuse, or extract a `process_record` that never touches SQS directly |
| SES dedup — idempotency gate protects S3, not SES if S3 upload crashes mid-way | Acceptable for now (at-least-once email); post-hire: add `email_sent` DB column |

---

## 6. Acceptance (mirrors issue #36)

- Message sent via `send_report_trigger` triggers Lambda end-to-end (PDF + email).
- Forced-failure message lands in DLQ after `maxReceiveCount` receives.
- Re-delivered duplicate message does NOT send a duplicate email (idempotency gate).
- All infra changes in IaC on `main`.

---

## 7. Implementation order (when ready)

1. Fix `VisibilityTimeout` → 120s in existing template.
2. Add DLQ to `sqs_queue.yml`.
3. Extract `process_record` from `worker.py` (remove SQS delete, wrap sync calls).
4. Write `lambda_sqs_worker.py` (handler shell + `asyncio.run`).
5. Add SAM Lambda resource + event-source mapping.
6. Smoke test locally (`sam local invoke` with synthetic SQS event JSON).
7. Deploy + verify DLQ with forced failure.
