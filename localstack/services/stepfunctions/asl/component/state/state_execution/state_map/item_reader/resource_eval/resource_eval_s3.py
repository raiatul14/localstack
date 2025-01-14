from __future__ import annotations

from typing import Callable, Final

from botocore.config import Config

from localstack.aws.connect import connect_to
from localstack.services.stepfunctions.asl.component.state.state_execution.state_map.item_reader.resource_eval.resource_eval import (
    ResourceEval,
)
from localstack.services.stepfunctions.asl.eval.environment import Environment
from localstack.utils.strings import camel_to_snake_case, to_str


class ResourceEvalS3(ResourceEval):
    _HANDLER_REFLECTION_PREFIX: Final[str] = "_handle_"
    _API_ACTION_HANDLER_TYPE = Callable[[Environment], None]

    @staticmethod
    def _get_s3_client():
        # TODO: adjust following multi-account and invocation region changes.
        return connect_to.get_client(
            service_name="s3",
            config=Config(parameter_validation=False),
        )

    @staticmethod
    def _handle_get_object(env: Environment) -> None:
        s3_client = ResourceEvalS3._get_s3_client()
        parameters = env.stack.pop()
        response = s3_client.get_object(**parameters)
        content = to_str(response["Body"].read())
        env.stack.append(content)

    @staticmethod
    def _handle_list_objects_v2(env: Environment) -> None:
        s3_client = ResourceEvalS3._get_s3_client()
        parameters = env.stack.pop()
        response = s3_client.list_objects_v2(**parameters)
        contents = response["Contents"]
        env.stack.append(contents)

    def _get_api_action_handler(self) -> ResourceEvalS3._API_ACTION_HANDLER_TYPE:
        api_action = camel_to_snake_case(self.resource.api_action).strip()
        handler_name = ResourceEvalS3._HANDLER_REFLECTION_PREFIX + api_action
        resolver_handler = getattr(self, handler_name)
        if resolver_handler is None:
            raise ValueError(f"Unknown s3 action '{api_action}'.")
        return resolver_handler

    def eval_resource(self, env: Environment) -> None:
        resolver_handler = self._get_api_action_handler()
        resolver_handler(env)
