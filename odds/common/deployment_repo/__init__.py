from ...common.select import select
from .config_deployment_repo import ConfigDeploymentRepo
from .deployment_repo import DeploymentRepo


deployment_repo: DeploymentRepo = select('DeploymentRepo', locals())()