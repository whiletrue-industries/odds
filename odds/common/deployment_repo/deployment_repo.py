from ..datatypes import Deployment


class DeploymentRepo:

    async def load_deployments(self) -> list[Deployment]:
        pass

    async def get_deployment(self, deployment_id: str) -> Deployment:
        pass