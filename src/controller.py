from database.model import Model
from dataobjects import ViewCallbacks
from gui.view import View


class Controller:
    def __init__(self, config: dict[str, any]) -> None:
        config_databases = config.pop("redis")
        
        self.model = Model(config_databases)
        self.view = View()

        view_callbacks = ViewCallbacks(
            self.model.users.get_user,
            self.model.users.create_user,
            self.model.snippets.get_next_snippet,
            self.model.users.update_user_state,
            self.model.markers.update_markers,
            self.model.markers.get_most_successful_markers,
            self.model.markers.get_least_successful_markers,
            self.model.users.get_friends,
            self.model.users.set_user_penalty,
            self.model.invitations.create_invitation_hash,
            self.model.invitations.get_invitee_id,
            self.model.users.make_friends,
            self.model.users.remove_friendship,
            self.model.users.get_user_by_id,
            self.model.invitations.remove_invitation_link
        )

        self.view.set_callbacks(view_callbacks)
        self.view.setup_routes()
