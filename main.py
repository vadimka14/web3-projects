import asyncio

from libs.eth_async.client import Client
from libs.eth_async.data.models import Networks, TokenAmount
from web3 import Web3

from tasks.base import Base
from data.config import PRIVATE_KEY
from data.models import Contracts
from tasks.odos import Odos


async def main():
    client = Client(private_key=PRIVATE_KEY, network=Networks.Linea)
    base = Base(client=client)
    odos = Odos(client=client)
    print(await odos.swap_eth_to_usdc(amount=TokenAmount(0.0001)))

if __name__ == '__main__':
    asyncio.run(main())

