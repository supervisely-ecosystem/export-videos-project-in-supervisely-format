import os
from distutils import util

from dotenv import load_dotenv
import supervisely as sly
from supervisely.app.v1.app_service import AppService
from supervisely.io.fs import mkdir

mkdir("debug", True)

if sly.is_development():
    load_dotenv("local.env")
    load_dotenv(os.path.expanduser("~/supervisely.env"))

api: sly.Api = sly.Api.from_env()
app_data = sly.app.get_data_dir()
sly.fs.clean_dir(app_data)

task_id = sly.env.task_id()
team_id = sly.env.team_id()
workspace_id = sly.env.workspace_id()
project_id = sly.env.project_id()
dataset_id = sly.env.dataset_id(raise_not_found=False)
if dataset_id is not None:
    dataset_id = [dataset_id]

# App settings
RESULT_DIR_NAME = "Export Videos in Supervisely format"
DOWNLOAD_ITEMS = bool(util.strtobool(os.environ.get("modal.state.items", "True")))
MAX_PARALLEL_VIDEO_DOWNLOADS = int(os.environ.get("modal.state.max_parallel_video_downloads", 5))
