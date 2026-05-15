from pydantic import BaseModel
from src.verity_portal.data_hub.projects.models import ProjectSensitivity

class ProjectMasterSchema(BaseModel):
    project_id: str
    name: str
    sensitivity: ProjectSensitivity = ProjectSensitivity.UNCLASSIFIED
    department: str | None = None
    export_control_status: str
