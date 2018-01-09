from steem import Steem
from steem.amount import Amount
from steem.account import Account
from dateutil.parser import parse
from os.path import expanduser, exists
from os import makedirs
from datetime import datetime
import logging

logger = logging.getLogger('steemrocks')
logger.setLevel(logging.INFO)
logging.basicConfig()


# This account will be monitored for their curation rewards
WATCH_ACCOUNT = "emrebeyler"

# If the checkpoint is reached, which account will get the steem?
PAY_ACCOUNT = "turbot"

# Every N Steem generated in terms of curation rewards
CHECKPOINT = 5

# Active key to make the transfer
ACTIVE_KEY = ""


def load_starting_point(fallback_starting_point=None):
    try:
        return int(open(CHECKPOINT).read())
    except FileNotFoundError as e:
        if not exists(CONFIG_PATH):
            makedirs(CONFIG_PATH)

            dump_starting_point(fallback_starting_point)
        return load_starting_point()


def dump_starting_point(starting_point):
    f = open(CHECKPOINT, 'w+')
    f.write(str(starting_point))
    f.close()


def vests_to_sp(vests, info):
    steem_per_mvests = (
        Amount(info["total_vesting_fund_steem"]).amount /
        (Amount(info["total_vesting_shares"]).amount / 1e6)
    )

    return vests / 1e6 * steem_per_mvests


def get_curation_rewards(account, info, checkpoint_val=100, starting_time=None):
    total_reward_in_rshares = 0
    total_reward_in_sp = 0
    checkpoint = checkpoint_val
    increase_per_checkpoint = checkpoint_val
    checkpoints = []
    history = account.history(filter_by=["curation_reward"])
    for curation_reward in history:
        if starting_time and parse(
                curation_reward["timestamp"]) < starting_time:
            continue

        curation_reward_rshares = Amount(curation_reward["reward"]).amount
        total_reward_in_rshares += curation_reward_rshares
        total_reward_in_sp += vests_to_sp(curation_reward_rshares, info)
        if int(total_reward_in_sp) % checkpoint < 10 and \
                int(total_reward_in_sp) >= checkpoint:
            checkpoints.append({
                "timestamp": curation_reward["timestamp"],
                "block": curation_reward["block"],
                "sub_total": round(total_reward_in_sp, 2),
                "checkpoint": checkpoint,
            })
            checkpoint += increase_per_checkpoint

    return total_reward_in_sp, total_reward_in_rshares, checkpoints
