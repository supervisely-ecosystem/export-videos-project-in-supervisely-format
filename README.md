<div align="center" markdown>
<img src="">

# Download Videos Project in Supervisely Format

<p align="center">
  <a href="#Overview">Overview</a>
  <a href="#How-To-Run">How To Run</a>
  <a href="#How-To-Use">How To Use</a>
</p>


[![](https://img.shields.io/badge/supervisely-ecosystem-brightgreen)](https://ecosystem.supervise.ly/apps/download-videos-in-supervisely-format)
[![](https://img.shields.io/badge/slack-chat-green.svg?logo=slack)](https://supervise.ly/slack)
![GitHub release (latest SemVer)](https://img.shields.io/github/v/release/supervisely-ecosystem/download-videos-in-supervisely-format)
[![views](https://app.supervise.ly/public/api/v3/ecosystem.counters?repo=supervisely-ecosystem/download-videos-in-supervisely-format&counter=views&label=views)](https://supervise.ly)
[![used by teams](https://app.supervise.ly/public/api/v3/ecosystem.counters?repo=supervisely-ecosystem/download-videos-in-supervisely-format&counter=downloads&label=used%20by%20teams)](https://supervise.ly)
[![runs](https://app.supervise.ly/public/api/v3/ecosystem.counters?repo=supervisely-ecosystem/download-videos-in-supervisely-format&counter=runs&label=runs&123)](https://supervise.ly)

</div>

## Overview

Export Supervisely videos project. You can learn more about format and its structure by reading [documentation](https://docs.supervise.ly/data-organization/00_ann_format_navi/06_supervisely_format_videos).


Application key points:
- Download annotations in `.json` and `.stl` formats


# How To Run 

1. Add  [Download Videos Project in Supervisely format](https://ecosystem.supervise.ly/apps/download-videos-in-supervisely-format)

<img data-key="sly-module-link" data-module-slug="supervisely-ecosystem/export-volume-project" src="https://i.imgur.com/DnAVFlZ.png" width="450px" style='padding-bottom: 20px'/>

2. Run app from the context menu of **Volume Project** or **Volumes Dataset** -> `Download via app` -> `Export Supervisely volume project in supervisely format`

<img src="https://imgur.com/xGX2kjq.png"/>

3. Define export settings in modal window and press the **Run** button

<div align="center" markdown>
<img src="https://i.imgur.com/ty0wHZJ.png" width="650"/>
</div>

# How To Use 

1. Wait for the app to process your data, once done, a link for download will become available
<img src="https://imgur.com/9SYRK5n.png"/>

2. Result archive will be available for download by link at `Tasks` page or from `Team Files` by the following path:


* `Team Files`->`Export-Supervisely-volumes-projects`->`<task_id>_<projectId>_<projectName>.tar`
<img src="https://imgur.com/02KtweO.png"/>
