from fastapi import Request
from starlette.datastructures import UploadFile
from typing import Any, Callable, Dict, Optional

from nicegui.events import UploadEventArguments, handle_event
from nicegui import app
from nicegui.elements.mixins.disableable_element import DisableableElement


class FilePicker(DisableableElement, component="file_pick.js"):
    def __init__(self, *, label: str = '', multiple: bool = False, accept_types=[""],
                 on_pick: Optional[Callable[..., Any]] = None,
                 on_delete: Optional[Callable[..., Any]] = None, ) -> None:
        super().__init__()

        self._props["label"] = label
        self._props["multiple"] = multiple
        self._props["accept"] = ", ".join(accept_types)

        # Define the endpoint URL
        self._props['url'] = f'/_nicegui/client/{self.client.id}/filepick/{self.id}'
        self._props['delete_url'] = f'/_nicegui/client/{self.client.id}/filedelete/{self.id}'

        @app.post(self._props['url'])
        async def pick_route(request: Request) -> Dict[str, str]:
            for data in (await request.form()).values():
                assert isinstance(data, UploadFile)
                args = UploadEventArguments(
                    sender=self,
                    client=self.client,
                    content=data.file,
                    name=data.filename or '',
                    type=data.content_type or '',
                )
                handle_event(on_pick, args)
            return {'pick': 'success'}

        @app.delete(self._props['delete_url'])  # Add a delete route
        async def delete_route(request: Request) -> Dict[str, str]:
            handle_event(on_delete, None)  # Trigger the on_delete callback
            return {'delete': 'success'}

    def _handle_delete(self) -> None:
        app.remove_route(self._props['url'])
        super()._handle_delete()