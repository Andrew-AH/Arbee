import os
import boto3


class MissingSecretsException(Exception):
    def __init__(self, missing_params):
        super().__init__(f"The following parameters were not found: {missing_params}")


def get_secrets(params: list[str]) -> dict[str, str]:
    ssm_client = boto3.client("ssm", region_name=os.getenv("AWS_DEFAULT_REGION"))
    response = ssm_client.get_parameters(Names=params, WithDecryption=True)

    secrets = {param["Name"]: param["Value"] for param in response.get("Parameters", [])}
    invalid_params = response.get("InvalidParameters", [])

    if invalid_params:
        raise MissingSecretsException(invalid_params)

    return secrets
