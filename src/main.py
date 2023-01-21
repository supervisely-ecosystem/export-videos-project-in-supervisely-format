import os
import supervisely as sly
from dotenv import load_dotenv
from distutils import util


if sly.is_development():
    load_dotenv("local.env")
    load_dotenv(os.path.expanduser("~/supervisely.env"))


try:
    os.environ['modal.state.items']
except KeyError:
    sly.logger.warn('The option to download project is not selected, project will be download with items')
    DOWNLOAD_ITEMS = True
else:
    DOWNLOAD_ITEMS = bool(util.strtobool(os.environ['modal.state.items']))

STORAGE_DIR = sly.app.get_data_dir()


class MyExport(sly.app.Export):
    def process(self, context: sly.app.Export.Context):

        api = sly.Api.from_env()

        project = api.project.get_info_by_id(id=context.project_id)
        project_name = project.name

        result_dir = os.path.join(STORAGE_DIR, f"{project.id}_{project_name}")
        sly.download_video_project(api=api, project_id=project.id, dest_dir=result_dir, dataset_ids=None,
                                download_videos=DOWNLOAD_ITEMS, log_progress=True)

        archive_name = f"{project.id}_{project_name}.tar.gz"
        result_archive = os.path.join(STORAGE_DIR, archive_name)
        sly.fs.archive_directory(result_dir, result_archive)
        sly.logger.info("Result directory is archived")

        return result_archive
    
app = MyExport()
app.run()
