"""
Access Service accounts for a channel - Only available to channel owners
"""

import logging

from tabulate import tabulate

from ..utils.format import comma_string_to_list
from .base import SubCommandBase

logger = logging.getLogger("repo_cli")


class SubCommand(SubCommandBase):
    name = "service-accounts"
    age_in_days = 30
    remove_token_keys = ["metadata"]

    feature_name = "channel_service_account"

    def main(self):
        if not self.check_for_feature():
            return
        self.check_for_login()

        if not self.args.channel:
            logger.error("Channel name is required")
            return
        if not self.args.user_id:
            user_id = self.get_user_id_from_channel(self.args.channel)
            if not user_id:
                return
        else:
            user_id = self.args.user_id

        # Check for parameter commands
        if self.args.list_tokens:
            self.list_tokens(self.args.channel, user_id)
            return
        elif self.args.list_user_ids:
            self.list_user_ids(self.args.channel)
            return
        elif self.args.create_token:
            if not self.args.name:
                logger.error("Token name is required")
                return
            self.create_token(
                self.args.channel,
                self.args.name,
                user_id,
                self.args.max_days,
                self.generate_resources_from_token_channels(),
            )
            return
        elif self.args.edit_token:
            if not self.args.token_id:
                logger.error("Token Id is required")
                return
            self.edit_token(
                self.args.channel,
                self.args.token_id,
                user_id,
                self.args.name,
                self.args.max_days,
                self.generate_resources_from_token_channels(),
            )
            return
        elif self.args.delete_token:
            if not self.args.token_id:
                logger.error("Token Id is required")
                return
            self.delete_token(self.args.channel, self.args.token_id, user_id)

    def check_for_feature(self):
        features = self.api.get_system_features()
        if features and self.feature_name in features:
            return True
        logger.error(
            "Service accounts feature is not enabled on {0}".format(self.api.base_url)
        )
        return False

    def check_for_login(self):
        if not self.api._jwt:
            logger.info("Authenticate for service account access")
            self.parent.auth_manager.interactive_get_token()

    def create_token(
        self, channel_name, token_name, user_id, max_days=None, resources=None
    ):
        data = self.api.create_channel_service_account_token(
            channel_name, user_id, token_name, max_days, resources
        )
        logger.info(
            "Token {0} succesfully created with id: {1}".format(
                data["token"], data["id"]
            )
        )

    def edit_token(
        self, channel_name, token_id, user_id, token_name, max_days=None, resources=None
    ):
        data = self.api.edit_channel_service_account_token(
            channel_name, user_id, token_id, token_name, max_days, resources
        )
        token_message = f"Token {data['token']} " if data.get("token") else "Token "
        logger.info(f"{token_message}successfully edited with id: {token_id}.")

    def delete_token(self, channel_name, token_id, user_id):
        self.api.delete_channel_service_account_token(channel_name, user_id, token_id)
        logger.info("Deleting token %s in channel %s", token_id, channel_name)

    def list_tokens(self, name, user_id=None):
        tokens = self.api.get_service_tokens_for_channel(name, user_id)

        if not tokens["items"]:
            logger.info("No tokens available for the specified channel.")
            return

        rows = [
            [value for key, value in item.items() if key not in self.remove_token_keys]
            for item in tokens["items"]
        ]
        headers = [
            key
            for key in tokens["items"][0].keys()
            if key not in self.remove_token_keys
        ]

        logger.info(tabulate(rows, headers=headers))

    def get_user_id_from_channel(self, channel_name):
        user_ids = self.api.get_user_id_channel_service_account(channel_name)
        if not user_ids or len(user_ids) > 1:
            logger.error("Provide Service Account user id")
            return False
        return user_ids[0]["id"]

    def list_user_ids(self, channel_name):
        user_ids = self.api.get_user_id_channel_service_account(channel_name)

        if not user_ids:
            logger.error("No user ids found")
            return

        rows = [x.values() for x in user_ids]
        headers = user_ids[0].keys()
        logger.info(tabulate(rows, headers=headers))

    def generate_resources_from_token_channels(self):
        token_channels = getattr(self.args, "token_channels", None)
        if not token_channels:
            token_channels = self.args.channel

        channel_names = list(set(comma_string_to_list(token_channels)))

        # Use permission from self.args or default to "read"
        permission = self.args.permission
        if not self.args.permission:
            permission = "read"

        # Generate the resources list
        resources = [
            {
                "resource_type": (
                    "subchannel" if self.api.is_subchannel(channel_name) else "channel"
                ),
                "resource_id": channel_name,
                "permission": permission,
            }
            for channel_name in channel_names
        ]

        return resources

    def add_parser(self, subparsers):
        self.subparser = subparsers.add_parser(
            self.name, help="Manage service accounts", description=__doc__
        )

        self.subparser.add_argument(
            "--channel", help="Channel name", type=str, required=True
        )

        self.subparser.add_argument(
            "--user-id", help="Service Account User ID", type=str
        )

        self.subparser.add_argument(
            "--list-user-ids",
            help="List service account user id of a channel",
            action="store_true",
        )

        self.subparser.add_argument(
            "--list-tokens",
            help="List all service account tokens linked with the channel",
            action="store_true",
        )

        # delete command
        self.subparser.add_argument(
            "--delete-token", help="Delete a service account token", action="store_true"
        )

        self.subparser.add_argument(
            "--token-id", help="Token ID", type=str, required=False
        )

        # edit / create command
        self.subparser.add_argument(
            "--create-token",
            help="Create a new service account token",
            action="store_true",
        )

        self.subparser.add_argument(
            "--edit-token", help="Edit a service account token", action="store_true"
        )

        self.subparser.add_argument(
            "--name", help="Token name", type=str, required=False
        )

        self.subparser.add_argument(
            "--token-channels",
            help="Create a token for individual or multiple channels Ex: channel1,channel2",
            type=str,
            required=False,
        )

        self.subparser.add_argument(
            "--permission",
            choices=[
                "read",
                "write",
                "manage",
            ],
            help="Read, Write or Manage permission for token",
            type=str,
            required=False,
        )

        self.subparser.add_argument(
            "--max-days",
            type=int,
            required=False,
            help="The maximum age in days that this token will be valid for (default value is"
            " %s days)" % self.age_in_days,
        )

        self.subparser.set_defaults(main=self.main)
