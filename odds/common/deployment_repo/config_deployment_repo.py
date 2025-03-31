from ..config import config
from ..datatypes import Deployment
from .deployment_repo import DeploymentRepo


class ConfigDeploymentRepo(DeploymentRepo):

    def __init__(self):
        self.deployments = None
        self.deployment_list = []

    async def load_deployments(self) -> list[Deployment]:
        if self.deployments is not None:
            return self.deployment_list
        self.deployments = {}
        deployments = config.deployments
        ret = [
            Deployment(
                deployment['id'],
                deployment['owner'],
                deployment['catalog_ids'], 
                deployment['agent_org_name'], 
                deployment['agent_catalog_descriptions'],
                deployment['ui_logo_html'],
                deployment['ui_display_html'],
                deployment['examples']
            )
            for deployment in deployments
        ]
        for deployment in ret:
            self.deployments[deployment.id] = deployment
            self.deployment_list.append(deployment)
        return ret

    async def get_deployment(self, deployment_id: str) -> Deployment:
        await self.load_deployments()
        return self.deployments.get(deployment_id)

    async def deployments_for_user(self, user_id: str) -> list[Deployment]:
        await self.load_deployments()
        return [d for d in self.deployment_list if user_id in d.owners]