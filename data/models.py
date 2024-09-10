import json
from dataclasses import dataclass

from libs.eth_async.utils.files import read_json
from libs.eth_async.classes import AutoRepr, Singleton
from libs.eth_async.data.models import RawContract, DefaultABIs

from data.config import ABIS_DIR


class Contracts(Singleton):
    WETH = RawContract(
        title='ETH',
        address='Linea ETH address',
        abi=read_json(path=(ABIS_DIR, 'WETH.json'))
    )
    USDC = RawContract(
        title='USDC',
        address='Linea usdc address ',
        abi=DefaultABIs.Token
    )

    ODOS = RawContract(
        title='odos',
        address='Linea odos Router address',
        abi=read_json(path=(ABIS_DIR, 'odos.json'))
    )




