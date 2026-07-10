"""CloduWatch alarm and metric testing purpose"""

import asyncio
import json
import argparse

from config import settings
from src.infrastructure.aws.aws_helper import AWSSessionManager
from src.infrastructure.aws.cloudwatch_client import CloudWatchClient


async def trigger_report():
    """Sets up a value for CloudWatch ReportGenerationFailures metric to check the HabitReportAlarm behaviour"""

    session_manager = AWSSessionManager()
    cw_client = CloudWatchClient(session_manager)

    for _ in range(2):
        await cw_client.put_metric(name="ReportGenerationFailures", value=1)


async def get_alarm_name():
    """"""

    parser = argparse.ArgumentParser(description="Get the CloudWatch alarm name for a given stack")
    parser.add_argument("stack_name", type=str, help="The name of the CloudFormation stack")
    session_manager = AWSSessionManager()
    cf_client = session_manager.session.client("cloudformation")
    async with cf_client as client:
        args = parser.parse_args()
        result = await client.describe_stacks(StackName=args.stack_name)
        print(json.dumps(result, indent=2, default=str))
        alarm_name = result["Stacks"][0]["Outputs"][1]["OutputValue"]
        print(alarm_name)
        return alarm_name


async def poll_transition(wait_time: int = 30):
    session_manager = AWSSessionManager()
    cw_client = CloudWatchClient(session_manager)
    alarm_name = await get_alarm_name()
    for _ in range(20):
        result = await cw_client.retrieve_metric_alarms([alarm_name])
        print(f"Result: {result}")
        if not result:
            continue
        state_value = result[0].get("StateValue")
        print(f"StateValue: {state_value}")
        if state_value == "ALARM":
            break
        await asyncio.sleep(wait_time)


async def main():
    await trigger_report()
    await poll_transition()


if __name__ == "__main__":
    asyncio.run(main())
