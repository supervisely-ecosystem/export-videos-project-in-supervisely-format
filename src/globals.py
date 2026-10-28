import os

import supervisely as sly
from dotenv import load_dotenv
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



def to_bool(value) -> bool:
    """Parse a modal.state flag ("True"/"False", any case); distutils is gone in Python 3.12+."""
    text = str(value).strip().lower()
    if text in ("1", "true", "yes", "on", "y", "t"):
        return True
    if text in ("0", "false", "no", "off", "n", "f"):
        return False
    raise ValueError(f"Expected a boolean, got {value!r}")


# App settings
RESULT_DIR_NAME = "Export Videos in Supervisely format"
DOWNLOAD_ITEMS = to_bool(os.environ.get("modal.state.items", "True"))
MAX_PARALLEL_VIDEO_DOWNLOADS = int(os.environ.get("modal.state.max_parallel_video_downloads", 5))

# Optional setting to split large archives into parts
SPLIT_RESULT = to_bool(os.environ.get("modal.state.split_result", "False"))
SPLIT_SIZE_GB = int(os.environ.get("modal.state.split_size", 5)) if SPLIT_RESULT else None
SPLIT_SIZE = SPLIT_SIZE_GB * (1024 ** 3) if SPLIT_SIZE_GB else None
