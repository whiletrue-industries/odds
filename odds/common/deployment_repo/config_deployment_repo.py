from ..config import config
from ..datatypes import Deployment
from .deployment_repo import DeploymentRepo


class ConfigDeploymentRepo(DeploymentRepo):

    def __init__(self):
        self.deployments = None
        self.deployment_list = []
        self.load_deployments()

    def load_deployments(self) -> list[Deployment]:
        if self.deployments is not None:
            return self.deployment_list
        self.deployments = {}
        deployments = config.deployments
        ret = [
            Deployment(
                deployment['id'], 
                deployment['catalog_ids'], 
                deployment['agent_org_name'], 
                deployment['agent_catalog_descriptions'],
                deployment['ui_logo_html'],
                deployment['ui_display_html'],
            )
            for deployment in deployments
        ]
        for deployment in ret:
            self.deployments[deployment.id] = deployment
            self.deployment_list.append(deployment)
        return ret

    def get_deployment(self, deployment_id: str) -> Deployment:
        return self.deployments.get(deployment_id)