import os
from distutils import util

from dotenv import load_dotenv
import supervisely as sly
from supervisely.app.v1.app_service import AppService
from supervisely.io.fs import mkdir

if sly.is_development():
    load_dotenv("local.env")
    load_dotenv(os.path.expanduser("~/supervisely.env"))

api: sly.Api = sly.Api.from_env()
my_app = AppService()

TEAM_ID = int(os.environ["context.teamId"])
WORKSPACE_ID = int(os.environ["context.workspaceId"])
PROJECT_ID = int(os.environ["modal.state.slyProjectId"])
DATASET_ID = os.environ.get("modal.state.slyDatasetId", None)

if DATASET_ID is not None:
    DATASET_ID = [int(DATASET_ID)]


TASK_ID = int(os.environ["TASK_ID"])
RESULT_DIR_NAME = "Export Videos in Supervisely format"
logger = sly.logger

try:
    os.environ["modal.state.items"]
except KeyError:
    logger.warn(
        "The option to download project is not selected, project will be download with items"
    )
    DOWNLOAD_ITEMS = True
else:
    DOWNLOAD_ITEMS = bool(util.strtobool(os.environ["modal.state.items"]))
