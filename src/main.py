import os

import supervisely as sly
from supervisely.project.download import download_async_or_sync
from supervisely.project.project_settings import LabelingInterface

import globals as g
import workflow as w
import utils as u


project = g.api.project.get_info_by_id(g.project_id)
project_name = project.name

project_meta_json = g.api.project.get_meta(g.project_id, with_settings=True)
project_meta = sly.ProjectMeta.from_json(project_meta_json)
is_multiview = project_meta.project_settings.labeling_interface == LabelingInterface.MULTIVIEW

result_dir = os.path.join(g.app_data, g.RESULT_DIR_NAME, project_name)
result_archive_path = os.path.join(g.app_data, g.RESULT_DIR_NAME)
if g.dataset_id is None:
    archive_name = f"{g.task_id}_{g.project_id}_{project_name}.tar"
    w.workflow_input(g.api, g.project_id, "project")
else:
    archive_name = f"{g.task_id}_{g.project_id}_{g.dataset_id[0]}_{project_name}.tar"
    w.workflow_input(g.api, g.dataset_id[0], "dataset")
result_archive = os.path.join(g.app_data, archive_name)
remote_archive_path = os.path.join(
    sly.team_files.RECOMMENDED_EXPORT_PATH, f"{g.RESULT_DIR_NAME}/{archive_name}"
)

download_async_or_sync(
    api=g.api,
    project_id=g.project_id,
    dest_dir=result_dir,
    dataset_ids=g.dataset_id,
    download_videos=g.DOWNLOAD_ITEMS,
    save_video_info=is_multiview,
    log_progress=True,
    semaphore=g.MAX_PARALLEL_VIDEO_DOWNLOADS,
)

if is_multiview:
    u.create_metadata_files(result_dir)
sly.fs.archive_directory(result_archive_path, result_archive)
sly.logger.info("Result directory is archived")

upload_progress = []
def _print_progress(monitor, upload_progress):
    if len(upload_progress) == 0:
        upload_progress.append(
            sly.Progress(
                message="Upload {!r}".format(archive_name),
                total_cnt=monitor.len,
                ext_logger=sly.logger,
                is_size=True,
            )
        )
    upload_progress[0].set_current_value(monitor.bytes_read)

file_info = g.api.file.upload(
    g.team_id,
    result_archive,
    remote_archive_path,
    lambda m: _print_progress(m, upload_progress),
)
sly.logger.info("Uploaded to Team-Files: {!r}".format(file_info.storage_path))
g.api.task.set_output_archive(
    g.task_id, file_info.id, archive_name, file_url=file_info.storage_path
)
w.workflow_output(g.api, file_info)
