from loguru import logger
from redis import Redis

from src.dataobjects import User
from src.gui.tools import int_to_base36


class InvitationManager:
    def __init__(self, redis_conf: dict[str, str], expiration_seconds: int = 60 * 60 * 24 * 7 * 4) -> None:
        self.redis = Redis(**redis_conf)
        logger.info("Invitations initialized.")

        self.expiration_seconds = expiration_seconds

    def create_invitation_hash(self, user: User) -> str:
        invitation_id = self.redis.incr("invitation_id_counter")
        invitation_hash = int_to_base36(hash(str(invitation_id)))
        invitation_key = f"invitation:{invitation_hash}"

        self.redis.set(invitation_key, user.db_id)
        self.redis.expire(invitation_key, self.expiration_seconds)

        return invitation_hash

    def get_invitee_id(self, invitation_hash: str) -> int | None:
        invitation_key = f"invitation:{invitation_hash}"
        if not self.redis.exists(invitation_key):
            return None

        invitee_id = int(self.redis.get(invitation_key))
        return invitee_id

    def remove_invitation_link(self, invitation_hash: str) -> None:
        invitation_key = f"invitation:{invitation_hash}"
        if not self.redis.exists(invitation_key):
            return

        self.redis.delete(invitation_key)
