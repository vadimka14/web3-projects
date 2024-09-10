import time
import asyncio
import random

import aiohttp
from web3.types import TxParams
from web3 import Web3

from tasks.base import Base
from libs.eth_async.data.models import TxArgs, TokenAmount, RawContract
from data.models import Contracts
from libs.eth_async import exceptions


class Odos(Base):
    async def quote(self, from_token: str | RawContract, to_token: str | RawContract, amount: int, slippage: float):
        url = "https://api.odos.xyz/sor/quote/v2"

        data = {
            "chainId": self.client.network.chain_id,
            "inputTokens": [
                {
                    "tokenAddress": from_token.address,
                    "amount": f"{amount.Wei}"
                }
            ],
            "outputTokens": [
                {
                    "tokenAddress": to_token.address,
                    "proportion": 1
                }
            ],
            "slippageLimitPercent": slippage,
            "userAddr": self.client.account.address,
            "referralCode": 0,
            "disableRFQs": True,
            "compact": True
        }

        async with aiohttp.ClientSession() as session:
            response = await session.post(
                url=url,
                headers={"Content-Type": "application/json"},
                json=data
            )

            if response.status == 200:
                response_data = await response.json()

                return response_data
            else:
                raise exceptions.HTTPException()

    async def assemble(self, path_id):
        url = "https://api.odos.xyz/sor/assemble"

        data = {
            "userAddr": self.client.account.address,
            "pathId": path_id,
            "simulate": False,
        }

        async with aiohttp.ClientSession() as session:
            response = await session.post(
                url=url,
                headers={"Content-Type": "application/json"},
                json=data
            )

            if response.status == 200:
                response_data = await response.json()

                return response_data
            else:
                raise exceptions.HTTPException()

    async def _swap(
            self,
            path: list[str],
            amount: TokenAmount | None = None,
            slippage: float = 0.3,
    ) -> str:
        from_token_address = Web3.to_checksum_address(path[0])
        to_token_address = Web3.to_checksum_address(path[-1])

        from_token_is_eth = from_token_address.upper() == Contracts.WETH.address.upper()

        from_token = await self.client.contracts.default_token(contract_address=from_token_address)
        from_token_name = await from_token.functions.symbol().call()

        to_token = await self.client.contracts.default_token(contract_address=to_token_address)
        to_token_name = await to_token.functions.symbol().call()

        failed_text = f'Failed swap {from_token_name} to {to_token_name} via Odos'

        contract = await self.client.contracts.get(contract_address=Contracts.ODOS)

        if not amount:
            amount = await self.client.wallet.balance(token=from_token)

        if not from_token_is_eth:
            if await self.approve_interface(
                token_address=from_token.address,
                spender=contract.address,
                amount=amount
            ):
                await asyncio.sleep(random.randint(5, 10))
            else:
                return f'{failed_text} | can not approve'

        qoute_data = await self.quote(from_token=from_token, to_token=to_token, amount=amount, slippage=slippage)

        transaction_data = await self.assemble(path_id=qoute_data["pathId"])

        transaction = transaction_data["transaction"]
        transaction["value"] = int(transaction["value"])

        tx = await self.client.transactions.sign_and_send(tx_params=transaction)
        receipt = await tx.wait_for_receipt(client=self.client, timeout=300)
        if receipt:
            return f'{amount.Ether} {from_token_name} was swapped to {to_token_name} via Odos: {tx.hash.hex()}'
        return f'{failed_text}!'

    async def swap_eth_to_usdc(
            self,
            amount: TokenAmount | None = None,
            slippage: float = 1.,
    ) -> str:
        return await self._swap(
            amount=amount,
            path=[Contracts.WETH.address, Contracts.USDC.address],
            slippage=slippage
        )

    async def swap_usdc_to_eth(
            self,
            amount: TokenAmount | None = None,
            slippage: float = 1.,
    ) -> str:
        return await self._swap(
            amount=amount,
            path=[Contracts.USDC.address, Contracts.WETH.address],
            slippage=slippage
        )
