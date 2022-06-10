"""
This script test a series of bank transfer transactions with single message between two accounts.
It takes two optional arguments namely -s(SENDER) and -r(RECEIVER).
"""
import argparse
import os
import sys
import time
import logging
from core.keys import keys_show
from modules.auth.query import account_type, query_account
from modules.bank.query import query_balances
from modules.bank.tx import tx_send
from utils import validate_num_txs, print_balance_deductions

HOME = os.getenv("HOME")
logging.basicConfig(format="%(message)s", level=logging.DEBUG)

PARSER = argparse.ArgumentParser(
    description="This program takes inputs for intializing multi message load test."
)
PARSER.add_argument(
    "-s",
    "--SENDER",
    type=account_type,
    default=keys_show("account1")[1]["address"],
    help="SENDER bech32 address",
)
PARSER.add_argument(
    "-r",
    "--RECEIVER",
    type=account_type,
    default=keys_show("account2")[1]["address"],
    help="RECEIVER bech32 address",
)
PARSER.add_argument(
    "-n",
    "--num_txs",
    type=validate_num_txs,
    default=10000,
    help="Number of transactions to be made, should be positive integer",
)
ARGS = PARSER.parse_args()
(SENDER,) = ARGS.sender
RECEIVER = ARGS.receiver
NUM_TXS = int(ARGS.num_txs)
AMOUNT = 1000000

if SENDER == RECEIVER:
    sys.exit(
        """Error: The values of arguments "sender" and "receiver"
             are equal make sure to set different values"""
    )

#### Fetch Balances from SENDER RECEIVER ####
STATUS, SENDER_BALANCE_OLD = query_balances(SENDER)
if not STATUS:
    sys.exit(SENDER_BALANCE_OLD)
SENDER_BALANCE_OLD = SENDER_BALANCE_OLD["balances"][0]["amount"]

STATUS, RECEIVER_BALANCE_OLD = query_balances(RECEIVER)
if not STATUS:
    sys.exit(RECEIVER_BALANCE_OLD)
RECEIVER_BALANCE_OLD = RECEIVER_BALANCE_OLD["balances"][0]["amount"]

# Fetching sequence numbers of to and from accounts
os.chdir(os.path.expanduser(HOME))
STATUS, SENDER_ACC = query_account(SENDER)
if not STATUS:
    sys.exit(SENDER_ACC)

STATUS, RECEIVER_ACC = query_account(RECEIVER)
if not STATUS:
    sys.exit(RECEIVER_ACC)

SENDER_ACC_SEQ, RECEIVER_ACC_SEQ = int(SENDER_ACC["sequence"]), int(
    RECEIVER_ACC["sequence"]
)

for i in range(NUM_TXS):
    seqto = SENDER_ACC_SEQ + i
    seqfrom = RECEIVER_ACC_SEQ + i
    STATUS, sTxto = tx_send(SENDER, RECEIVER, AMOUNT, 100000, False, seqto)
    if not STATUS:
        logging.error("%s", sTxto)
    else:
        logging.info("TX HASH to :: %s", sTxto["txhash"])
    STATUS, sTxfrom = tx_send(RECEIVER, SENDER, AMOUNT, 100000, False, seqfrom)
    if not STATUS:
        logging.error("%s", sTxfrom)
    else:
        logging.info("TX HASH from :: %s", sTxto["txhash"])

logging.info("waiting for tx confirmation, avg time is 7s.")
time.sleep(7)

#### Print Balances ####
STATUS, SENDER_BALANCE_UPDATED = query_balances(SENDER)
if not STATUS:
    sys.exit(SENDER_BALANCE_UPDATED)
SENDER_BALANCE_UPDATED = SENDER_BALANCE_UPDATED["balances"][0]["amount"]

STATUS, RECEIVER_BALANCE_UPDATED = query_balances(RECEIVER)
if not STATUS:
    sys.exit(RECEIVER_BALANCE_UPDATED)
RECEIVER_BALANCE_UPDATED = RECEIVER_BALANCE_UPDATED["balances"][0]["amount"]

SENDER_DIFF = int(SENDER_BALANCE_OLD) - int(SENDER_BALANCE_UPDATED)
RECEIVER_DIFF = int(RECEIVER_BALANCE_OLD) - int(RECEIVER_BALANCE_UPDATED)

print_balance_deductions("SENDER", SENDER_DIFF)
print_balance_deductions("RECEIVER", RECEIVER_DIFF)
