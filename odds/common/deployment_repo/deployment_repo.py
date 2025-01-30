from ..datatypes import Deployment


class DeploymentRepo:

    def load_deployments(self) -> list[Deployment]:
        pass

    def get_deployment(self, deployment_id: str) -> Deployment:
        pass