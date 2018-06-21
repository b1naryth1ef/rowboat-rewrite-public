"""
Plugin for creating and tracking infractions

!ban <user> [reason]
!forceban <snowflake> [reason]
!unban <user|snowflake> [reason]
!mute <user> [reason]
!tempmute <user> <duration> [reason]
!unmute <user> [reason]
!kick <user> [reason]
!warn <user> [reason]
!tempban <user> <duration> [reason]

!infractions export [txt|json|csv]
!infraactions info/lookup <id>
!infractions search (argparse)
!infractions edit (argparse)
!infractions reason (argparse, <id> <reason> --force)
!infractions bulk (argparse)

Config:
    ack_actions = Field(bool, default=True)
    ack_actions_use_reaction = Field(bool, default=False)
    ack_actions_delete_after = Field(int, default=0)

    notify_user = Field(bool, default=False)

    mute_role = Field(snowflake, default=None)
"""
