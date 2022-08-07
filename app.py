import aws_cdk as cdk
from aws_cdk import (
    Stack,
    aws_apigateway as apigw,
    aws_lambda as lambda_,
    Duration,
    Tags,
)
from constructs import Construct


PROJECT_NAME = "Asakatsu"


class AsakatsuStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        layer = lambda_.LayerVersion(
            self, f"lyr_{PROJECT_NAME}Service_cdk",
            code=lambda_.Code.from_asset("layer"),
            layer_version_name=f"lyr_{PROJECT_NAME}Service_cdk",
            compatible_runtimes=[lambda_.Runtime.PYTHON_3_9],
        )

        fn = lambda_.Function(
            self, f"lmd_{PROJECT_NAME}Service_cdk",
            code=lambda_.Code.from_asset("src"),
            handler="lambda_function.lambda_handler",
            runtime=lambda_.Runtime.PYTHON_3_9,
            timeout=Duration.seconds(30),
            memory_size=256,
            function_name=f"lmd_{PROJECT_NAME}Service_cdk",
            layers=[layer]
        )

        api = apigw.LambdaRestApi(
            self, f"api_{PROJECT_NAME}Service_cdk",
            handler=fn,
            binary_media_types=["*/*"],
            rest_api_name=PROJECT_NAME
        )

        stamp = api.root.add_resource("stamp")
        stamp.add_method("GET")
        cdk.CfnOutput(
            self, "stamp_url",
            value=stamp.path,
        )


app = cdk.App()
apigw_stack = AsakatsuStack(app, "AsakatsuStack", stack_name="AsakatsuStack")
Tags.of(apigw_stack).add("Project", PROJECT_NAME)
Tags.of(apigw_stack).add("Type", "Pro")
Tags.of(apigw_stack).add("Construct", "AsakatsuStack")
Tags.of(apigw_stack).add("Creator", "cdk")
app.synth()
