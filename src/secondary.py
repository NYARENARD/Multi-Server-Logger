import os

config = {
    "token_selfbot" : os.getenv("TOKEN_SELFBOT"),
    "log_guild" : int(os.getenv("LOG_GUILD")),
    "aux_channel" : int(os.getenv("AUX_CHANNEL"))
}