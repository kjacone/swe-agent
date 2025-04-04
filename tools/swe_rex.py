import asyncio
from swerex.deployment.local import LocalDeployment
from swerex.runtime.abstract import CreateBashSessionRequest, BashAction


async def run_express_app():
    deployment = LocalDeployment()
    await deployment.start()
    runtime = deployment.runtime

    # Create a bash session
    await runtime.create_session(CreateBashSessionRequest())

    # Navigate to the directory containing app.js
    await runtime.run_in_session(
        BashAction(
            command="cd /Users/macbook/machine-learning/projects/swe/agent/sub_graphs/swe/app"
        )
    )

    # Install npm packages
    await runtime.run_in_session(BashAction(command="npm install"))

    # Run the Express.js application
    await runtime.run_in_session(BashAction(command="node app.js"))


asyncio.run(run_express_app())
