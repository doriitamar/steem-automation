const steem = require('steem');


function getHistory(account, from, limit, reward, opCount) {
    steem.api.getAccountHistory(account, from, limit, function (err, result) {
        if (err) {
            console.log('ERR');
            console.log(err);
            return
        }
        result.forEach(function (tx) {
            var op = tx[1].op;
            var op_type = op[0];
            var op_value = op[1];
            if (op_type == "producer_reward") {
                reward = reward + parseFloat(op_value.vesting_shares.replace(" VESTS", ""));
            }

        });
        if (from > 0) {
            var fromOp = from - limit;
            if ((from - limit) < limit) {
                limit = from - limit;
            }

            getHistory(account, fromOp, limit, reward, opCount);
        } else {
            console.log("----------")
            steem.api.getDynamicGlobalProperties(function (err, result) {
                var totalVestingFundSteem = parseFloat(result.total_vesting_fund_steem.replace(" STEEM", ""));
                var totalVestingShares = parseFloat(result.total_vesting_shares.replace(" VESTS", ""));
                var steemPerMvest = totalVestingFundSteem / (totalVestingShares / 1e6);
                var estimatedSp = reward / 1e6 * steemPerMvest;
                console.log("Estimated (Total) SP: " + estimatedSp);
                console.log("Total Vesting Shares: " + totalVestingShares);
            });
        }
    });
}


function producerRewardHistory(account) {
    steem.api.getAccountHistory(account, -1, 0, function (err, result) {
        opCount = result[0][0];
        console.log("Total operation count: " + opCount);
        return getHistory(account, opCount, 1000, 0, opCount);
    });

}


producerRewardHistory(process.argv[2]);
