from steem import Steem
from steem.amount import Amount
from steem.account import Account
from steem.commit import Commit

from pymongo import MongoClient
from settings import (
    WATCH_ACCOUNT, ACTIVE_KEY, PAY_ACCOUNT, CHECKPOINT_VAL,
    STARTING_TIME, BANK_ACCOUNT, MEMO_TEMPLATE, TRANSFER_AMOUNT_PER_ROUND,
    MONGO_URI, NODES)
from utils import get_curation_rewards
from dateutil.parser import parse


import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)
logging.basicConfig()


class TransferOnCuration:

    def __init__(self, steemd, mongo_uri, watch_account="utopian-io",
                 pay_account="utopian.org", bank_account="utopian.com",
                 memo_template=None, transfer_amount_per_round=None):
        self.steemd = steemd
        self.commit = Commit(self.steemd)
        self.mongo = MongoClient(mongo_uri)
        self.watch_account = watch_account
        self.pay_account = pay_account
        self.bank_account = bank_account
        self.memo_template = memo_template
        self.transfer_amount_per_round = transfer_amount_per_round
        self.db = self.mongo['utopian-transfer-on-curations']
        self.transfers = self.db['transfers']

    def fill_transfer_history(self):
        acc = Account(self.bank_account, steemd_instance=self.steemd)

        transfers = acc.history(filter_by=["transfer"])
        logger.info("Fetching transfer history of %s.", self.watch_account)
        for transfer in transfers:

            # only interested in STEEM asset.
            amount = Amount(transfer["amount"])
            if amount.asset != "STEEM":
                continue

            # only interested in
            # transfers going to pay account
            if transfer["to"] != self.pay_account:
                continue

            if not self.transfers.find_one({
                "from": transfer["from"],
                "to": transfer["to"],
                "memo": transfer["memo"],
            }):
                if self.memo_template == transfer["memo"]:
                    new_entry = self.transfers.insert({
                        "from": transfer["from"],
                        "to": transfer["to"],
                        "memo": transfer["memo"],
                        "timestamp": transfer["timestamp"],
                    })

                    logger.info(new_entry)

        logger.info("Populated transfer data.")

    def get_last_transfer(self):
        if self.transfers.find({
            "from": self.bank_account,
            "to": self.pay_account,
        }).count() == 0:
            return None

        last_transfer = self.transfers.find({
                "from": self.bank_account,
                "to": self.pay_account,
            }).sort("timestamp")

        return last_transfer[0]

    def run(self, checkpoint_val=None, starting_time=None,
            force_starting_time=False):
        self.fill_transfer_history()
        info = self.steemd.get_dynamic_global_properties()

        logger.info("Fetching old transfers")
        last_transfer = self.get_last_transfer()

        if last_transfer and not force_starting_time:
            starting_time = parse(last_transfer["timestamp"])
            logger.info("Setting starting_time as %s" % starting_time)

        logger.info("Fetching curation rewards")
        total_sp, total_vests, checkpoints = get_curation_rewards(
            Account(self.watch_account, steemd_instance=self.steemd),
            info,
            checkpoint_val=checkpoint_val,
            starting_time=starting_time,
        )

        if len(checkpoints) == 0 or len(checkpoints) > 1:
            logger.error(
                "Stopped. Waiting for more SP. Current: %s", total_sp)
            logger.error(checkpoints)
            return

        self.commit.transfer(
            self.pay_account,
            self.transfer_amount_per_round,
            memo=MEMO_TEMPLATE,
            asset="STEEM",
            account=self.bank_account
        )
        logger.info(
            "Sent %s STEEM to %s." % (
                self.transfer_amount_per_round, self.pay_account))


if __name__ == '__main__':
    s = Steem(nodes=NODES, keys=[ACTIVE_KEY])
    transfer_on_curation = TransferOnCuration(
        s,
        MONGO_URI,
        watch_account=WATCH_ACCOUNT,
        pay_account=PAY_ACCOUNT,
        bank_account=BANK_ACCOUNT,
        memo_template=MEMO_TEMPLATE,
        transfer_amount_per_round=TRANSFER_AMOUNT_PER_ROUND,
    )
    transfer_on_curation.run(checkpoint_val=CHECKPOINT_VAL,
                             starting_time=parse(STARTING_TIME),
                             force_starting_time=False)
