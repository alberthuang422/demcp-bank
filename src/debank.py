from typing import Any
import httpx
from mcp.server.fastmcp import FastMCP

# Initialize FastMCP server
mcp = FastMCP("debank",host="0.0.0.0",port=8080)

ACCESS_KEY = "c999205e9185cef6e77e536bdd850db0831dffc9"
BASE_URL = "https://pro-openapi.debank.com"
# USER_AGENT = "DEMCP-DEBANK/1.0"


async def make_nws_request(url: str) -> dict[str, Any] | None:
    """Make a request to the NWS API with proper error handling."""
    headers = {
        # "User-Agent": USER_AGENT,
        "Accept": "application/json",
        "AccessKey": ACCESS_KEY
    }
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, headers=headers, timeout=30.0)
            response.raise_for_status()
            return response.json()
        except Exception:
            return None

# TAG：chain-api
# curl -X 'GET' 'https://pro-openapi.debank.com/v1/chain?id=eth' -H 'accept: application/json' -H 'AccessKey: c999205e9185cef6e77e536bdd850db0831dffc9'
@mcp.tool(
    description="This API endpoint retrieves blockchain information using a GET request to /v1/chain with a required id parameter, "+
                "returning details like the chain's ID, name, logo URL, native and wrapped token IDs, and pre-execution support status."
)
async def get_chain_info(id: str):
    """Get chain information from DeBank API.

    Args:
        id: Chain identifier (e.g. eth, bsc, xdai)
    """
    return await make_nws_request(f"{BASE_URL}/v1/chain?id={id}")


# curl -X 'GET' 'https://pro-openapi.debank.com/v1/chain/list' -H 'accept: application/json' -H 'AccessKey: c999205e9185cef6e77e536bdd850db0831dffc9'
@mcp.tool(
    description="This API endpoint retrieves a list of supported blockchains using a GET request to /v1/chain/list without parameters, "+
                "returning an array of objects with details like chain ID, name, logo URL, native and wrapped token IDs, and pre-execution support status."
)
async def get_chain_list():
    """
    Get a list of supported blockchains from DeBank API.
    """
    return await make_nws_request(f"{BASE_URL}/v1/chain/list")

# TAG：protocl api
# curl -X 'GET' 'https://pro-openapi.debank.com/v1/protocol?id=compound' -H 'accept: application/json' -H 'AccessKey: c999205e9185cef6e77e536bdd850db0831dffc9'
@mcp.tool(
    description="This API endpoint retrieves protocol information using a GET request to /v1/protocol with a required id parameter, "+
                "returning an object with details like protocol ID, chain ID, name, logo URL, site URL, portfolio support status, and TVL (user deposit value)."
)
async def get_protocol_info(id: str):
    """
   
    id : required, eg: bsc_pancakeswap, curve, uniswap
    """
    return await make_nws_request(f"{BASE_URL}/v1/protocol?id={id}")

# curl -X GET "https://pro-openapi.debank.com/v1/protocol/list?chain_id=eth" \ -H "accept: application/json" -H 'AccessKey: 72e3d39ee2e237c98a2eea7fcfae563b0978849b'
# @mcp.tool(
#     description="This API endpoint retrieves a list of protocols on a specified blockchain using a GET request to /v1/protocol/list with a required chain_id parameter, "+
#                 "returning an array of objects with details like protocol ID, chain ID, name, logo URL, site URL, portfolio support status, and TVL (user deposit value)."
# )
# async def get_protocol_list(chain_id: str):
#     """
#     chain_id : required, chain id, eg: eth, bsc, xdai, for more info.
#     """
#     return await make_nws_request(f"{BASE_URL}/v1/protocol/list?chain_id={chain_id}")

@mcp.tool(
    description="Get protocols，sorted by TVL"
)
async def get_protocols_list(chain_id: str, limit: int = 20):
    """Get top protocols by TVL for a specific chain.
    
    Args:
        chain_id: Chain identifier (e.g. eth, bsc)
        limit: Number of top protocols to return (default: 20)
    """
    protocols = await make_nws_request(f"{BASE_URL}/v1/protocol/list?chain_id={chain_id}")
    if protocols:
        # Sort protocols by TVL in descending order
        sorted_protocols = sorted(protocols, key=lambda x: x.get('tvl', 0), reverse=True)
        # Return top N protocols
        return sorted_protocols[:limit]
    return None


# curl -X GET "https://pro-openapi.debank.com/v1/protocol/top_holders?id=eth" \
#      -H "accept: application/json" -H 'AccessKey: YOUR_ACCESSKEY'
@mcp.tool(
    description="This API endpoint retrieves the top holders of a protocol using a GET request to /v1/protocol/top_holders with a required id parameter and optional start (offset, default 0, max 1000) and limit (size, default 100, max 100) parameters, "+
                "returning an array of address-value pairs in USD.  "
)
async def get_protocol_top_holders(id: str, start: int | None = None, limit: int | None = None):
    """
    Args:
        id : string required, protocol id
        start: integer offset, default is 0, max is 1000.
        limit: integer limit size, default is 100, max is 100.
    """
    url = f"{BASE_URL}/v1/protocol/top_holders?id={id}"
    if start is not None:
        url += f"&start={start}"
    if limit is not None:
        url += f"&limit={limit}"
    return await make_nws_request(url)


# TAG： POOL
# curl -X GET "https://pro-openapi.debank.com/v1/pool?id=eth" \
#      -H "accept: application/json" -H 'AccessKey: YOUR_ACCESSKEY'
@mcp.tool(
    description="This API endpoint retrieves information about a specific pool using a GET request to /v1/pool with required id (pool ID) and chain_id (chain ID) parameters, "+
                "returning an object with details like pool ID, chain ID, protocol ID, contract IDs, name, and stats (deposit USD value, total user count, and valuable user count with USD value over $100)."
)
async def get_pool_info(id: str, chain_id: str):
    """
    Args:
        id : required, pool_id, eg: 0x00000000219ab540356cbb839cbe05303d7705fa
        chain_id : required, chain id, eg: eth, bsc, xdai, for more info.
    """
    return await make_nws_request(f"{BASE_URL}/v1/pool?id={id}&chain_id={chain_id}")


# TAG: TOKEN
# curl -X 'GET' 'https://pro-openapi.debank.com/v1/token?chain_id=eth&id=eth' \
#  -H 'accept: application/json' -H 'AccessKey: YOUR_ACCESSKEY'
@mcp.tool()
async def get_token_infomation(chain_id: str, id: str):
    """
    Args:
        chain_id : required, chain id, eg: eth, bsc, xdai, for more info.
        id : required, - The address of the token contract or a native token id (eth, matic, bsc).
    """
    return await make_nws_request(f"{BASE_URL}/v1/token?chain_id={chain_id}&id={id}")
    

# curl -X GET "https://pro-openapi.debank.com/v1/token/top_holders?chain_id=celo&id=celo&start=2&limit=1" \
#      -H "accept: application/json" -H 'AccessKey: YOUR_ACCESSKEY'
@mcp.tool(
    description="This API endpoint retrieves the top holders of a token using a GET request to /v1/token/top_holders with required chain_id and id parameters and optional start (offset, default 0, max 10000) and limit (size, default 100, max 100) parameters, "+
                "returning an array of address-amount pairs in reverse order of holding token amount."
)
async def get_token_top_holders(chain_id: str, id: str, start=0, limit=100):
    """
    Args:
        chain_id : required, chain id, eg: eth, bsc, xdai, for more info.
        id : required, - The address of the token contract or a native token id (eth, matic, bsc).
        start: integer offset, default is 0, max is 10000.
        limit: integer limit size, default is 100, max is 100.
    """
    
    # 构造 URL
    url = f"{BASE_URL}/v1/token/top_holders?chain_id={chain_id}&id={id}&start={start}&limit={limit}"

    # 发送请求
    return await make_nws_request(url)



@mcp.tool(
    description="This API endpoint retrieves a token's historical price using a GET request to /v1/token/history_price with required chain_id, id (token address or native token ID), and date_at (UTC time zone, e.g., 2023-05-18) parameters, "+
                "returning the price at the specified time."
)
async def get_token_history_price(chain_id: str, id: str, date_at: str):
    """
    Args:
        id : string required, token address, also support native token id, eg. eth, bsc
        chain_id : required, chain id, eg: eth, bsc, xdai, for more info.
        date_at: string required, UTC time zone. eg. 2023-05-18
    """
    return await make_nws_request(f"{BASE_URL}/v1/token/history_price?chain_id={chain_id}&id={id}&date_at={date_at}")


# TAG User
# curl -X 'GET' 'https://pro-openapi.debank.com/v1/user/used_chain_list?id=0xcfeaead4947f0705a14ec42ac3d44129e1ef3ed5' \
#  -H 'accept: application/json' -H 'AccessKey: YOUR_ACCESSKEY'
@mcp.tool(
    description="Get a list of blockchains used by a user using a GET request to /v1/user/used_chain_list with a required id parameter (user address), " +
                "returning an array of objects with details like chain ID, name, logo URL, native token ID, and more."
)
async def get_user_used_chain_list(id: str):
    """
    Args:
        id : string required, user address
    """
    return await make_nws_request(f"{BASE_URL}/v1/user/used_chain_list?id={id}")



# curl -X 'GET' \
# https://pro-openapi.debank.com/v1/user/chain_balance?id=0x5853ed4f26a3fcea565b3fbc698bb19cdf6deb85&chain_id=eth' \
# -H 'accept: application/json' -H 'AccessKey: YOUR_ACCESSKEY'
@mcp.tool(
    description="Get a user's balance on a specific blockchain using a GET request to /v1/user/chain_balance with required id (user address) and chain_id parameters, " +
                "returning the USD value of the user's assets on the specified blockchain."
)
async def get_user_chain_balance(id: str, chain_id: str):
    """
    Args:
        id : string required, user address
        chain_id : string required, chain id, eg: eth, bsc, xdai, for more info.
    """
    return await make_nws_request(f"{BASE_URL}/v1/user/chain_balance?id={id}&chain_id={chain_id}")

@mcp.tool(
    description="Get a user's token balance for a specific token on a blockchain using a GET request to /v1/user/token_balance with required id, chain_id, and token_id parameters, " +
                "returning details about the token balance including amount and USD value."
)
async def get_user_token_balance(id: str, chain_id: str, token_id: str):
    """
    Args:
        id : string required, user address
        chain_id : string required, chain id, eg: eth, bsc, xdai
        token_id : string required, token id
    """
    return await make_nws_request(f"{BASE_URL}/v1/user/token_balance?id={id}&chain_id={chain_id}&token_id={token_id}")

@mcp.tool(
    description="Get a list of token balances for a user on a specific blockchain using a GET request to /v1/user/token_list with required id and chain_id parameters, " +
                "returning an array of token objects with details like token ID, name, symbol, price, and balance amount."
)
async def get_user_token_list(id: str, chain_id: str):
    """
    Args:
        id : string required, user address
        chain_id : string required, chain id, eg: eth, bsc, xdai
    """
    return await make_nws_request(f"{BASE_URL}/v1/user/token_list?id={id}&chain_id={chain_id}")

@mcp.tool(
    description="Get a list of token balances for a user across all supported chains using a GET request to /v1/user/all_token_list with a required id parameter and optional chain_ids parameter, " +
                "returning an array of token objects grouped by chain."
)
async def get_all_token_list(id: str, chain_ids: str = None):
    """
    Args:
        id : string required, user address
        chain_ids : string optional, comma-separated list of chain ids, eg: eth,bsc,xdai
    """
    url = f"{BASE_URL}/v1/user/all_token_list?id={id}"
    if chain_ids:
        url += f"&chain_ids={chain_ids}"
    return await make_nws_request(url)

@mcp.tool(
    description="Get a list of NFTs owned by a user on a specific blockchain using a GET request to /v1/user/nft_list with required id and chain_id parameters, " +
                "returning an array of NFT objects with details like collection info, token ID, and value."
)
async def get_user_nft_list(id: str, chain_id: str):
    """
    Args:
        id : string required, user address
        chain_id : string required, chain id, eg: eth, bsc, xdai
    """
    return await make_nws_request(f"{BASE_URL}/v1/user/nft_list?id={id}&chain_id={chain_id}")

@mcp.tool(
    description="Get a user's positions in a specific protocol using a GET request to /v1/user/protocol with required id (user address) and protocol_id parameters, " +
                "returning detailed information about the user's assets, investments, and rewards in the specified protocol."
)
async def get_user_protocol(id: str, protocol_id: str):
    """
    Args:
        id : string required, user address
        protocol_id : string required, protocol id
    """
    return await make_nws_request(f"{BASE_URL}/v1/user/protocol?id={id}&protocol_id={protocol_id}")

@mcp.tool(
    description="Get a list of NFTs owned by a user across all supported chains using a GET request to /v1/user/all_nft_list with a required id parameter and optional chain_ids parameter, " +
                "returning an array of NFT objects grouped by chain."
)
async def get_all_nft_list(id: str, chain_ids: str = None):
    """
    Args:
        id : string required, user address
        chain_ids : string optional, comma-separated list of chain ids, eg: eth,bsc,xdai
    """
    url = f"{BASE_URL}/v1/user/all_nft_list?id={id}"
    if chain_ids:
        url += f"&chain_ids={chain_ids}"
    return await make_nws_request(url)

@mcp.tool(
    description="Get a user's transaction history on a specific blockchain using a GET request to /v1/user/history_list with required id and chain_id parameters, " +
                "returning an array of transaction objects with details like transaction hash, time, and more."
)
async def get_user_history_list(id: str, chain_id: str, page_count: int = None, start_time: int = None):
    """
    Args:
        id : string required, user address
        chain_id : string required, chain id, eg: eth, bsc, xdai
        page_count : int optional, number of pages to return
        start_time : int optional, unix timestamp to start from
    """
    url = f"{BASE_URL}/v1/user/history_list?id={id}&chain_id={chain_id}"
    if page_count is not None:
        url += f"&page_count={page_count}"
    if start_time is not None:
        url += f"&start_time={start_time}"
    return await make_nws_request(url)

@mcp.tool(
    description="Get a user's transaction history across all supported chains using a GET request to /v1/user/history with required id parameter and optional chain_ids, page_count, and start_time parameters, " +
                "returning an array of transaction objects grouped by chain."
)
async def get_history_list(id: str, chain_ids: str = None, page_count: int = None, start_time: int = None):
    """
    Args:
        id : string required, user address
        chain_ids : string optional, comma-separated list of chain ids, eg: eth,bsc,xdai
        page_count : int optional, number of pages to return
        start_time : int optional, unix timestamp to start from
    """
    url = f"{BASE_URL}/v1/user/history?id={id}"
    if chain_ids:
        url += f"&chain_ids={chain_ids}"
    if page_count is not None:
        url += f"&page_count={page_count}"
    if start_time is not None:
        url += f"&start_time={start_time}"
    return await make_nws_request(url)

@mcp.tool(
    description="Get a user's total balance across all supported chains using a GET request to /v1/user/total_balance with a required id parameter and optional chain_ids parameter, " +
                "returning the total USD value and a breakdown by chain."
)
async def get_user_total_balance(id: str, chain_ids: str = None):
    """
    Args:
        id : string required, user address
        chain_ids : string optional, comma-separated list of chain ids, eg: eth,bsc,xdai
    """
    url = f"{BASE_URL}/v1/user/total_balance?id={id}"
    if chain_ids:
        url += f"&chain_ids={chain_ids}"
    return await make_nws_request(url)

@mcp.tool(
    description="Get a user's 24-hour net curve data on a specific blockchain using a GET request to /v1/user/chain_net_curve with required id and chain_id parameters, " +
                "returning an array of timestamp-value pairs showing the user's balance over time."
)
async def get_user_chain_net_curve(id: str, chain_id: str):
    """
    Args:
        id : string required, user address
        chain_id : string required, chain id, eg: eth, bsc, xdai
    """
    return await make_nws_request(f"{BASE_URL}/v1/user/chain_net_curve?id={id}&chain_id={chain_id}")

@mcp.tool(
    description="Get a user's 24-hour net curve data across all chains using a GET request to /v1/user/total_net_curve with a required id parameter and optional chain_ids parameter, " +
                "returning an array of timestamp-value pairs showing the user's total balance over time."
)
async def get_user_total_net_curve(id: str, chain_ids: str = None):
    """
    Args:
        id : string required, user address
        chain_ids : string optional, comma-separated list of chain ids, eg: eth,bsc,xdai
    """
    url = f"{BASE_URL}/v1/user/total_net_curve?id={id}"
    if chain_ids:
        url += f"&chain_ids={chain_ids}"
    return await make_nws_request(url)

@mcp.tool(
    description="Get a user's detailed protocol portfolios on a specified chain using a GET request to /v1/user/complex_protocol_list with required chain_id and id parameters, " +
                "returning an array of objects with protocol details like ID, chain ID, name, logo URL, site URL, portfolio support status, and a list of portfolio items (cached data, near real-time within 1 minute, guaranteed update within 12 hours)."
)
async def get_user_complex_protocol_list(chain_id: str, id: str):
    """
    Args:
        chain_id : string required, chain id, eg: eth, bsc, xdai
        id : string required, user address
    """
    return await make_nws_request(f"{BASE_URL}/v1/user/complex_protocol_list?id={id}&chain_id={chain_id}")

@mcp.tool(
    description="Get a user's detailed protocol portfolios across all supported chains using a GET request to /v1/user/all_complex_protocol_list with a required id parameter and optional chain_ids parameter, " +
                "returning an array of objects with protocol details like ID, chain ID, name, logo URL, site URL, portfolio support status, and a list of portfolio items across all chains."
)
async def get_all_complex_protocol_list(id: str, chain_ids: str = None):
    """
    Args:
        id : string required, user address
        chain_ids : string optional, comma-separated list of chain ids, eg: eth,bsc,xdai
    """
    url = f"{BASE_URL}/v1/user/all_complex_protocol_list?id={id}"
    if chain_ids:
        url += f"&chain_ids={chain_ids}"
    return await make_nws_request(url)

@mcp.tool(
    description="Get a user's simple protocol list (balance information) on a specific blockchain using a GET request to /v1/user/simple_protocol_list with required id and chain_id parameters, " +
                "returning an array of objects with protocol details and balance information."
)
async def get_user_simple_protocol_list(id: str, chain_id: str):
    """
    Args:
        id : string required, user address
        chain_id : string required, chain id, eg: eth, bsc, xdai
    """
    return await make_nws_request(f"{BASE_URL}/v1/user/simple_protocol_list?id={id}&chain_id={chain_id}")

@mcp.tool(
    description="Get a user's simple protocol list (balance information) across all supported chains using a GET request to /v1/user/all_simple_protocol_list with a required id parameter and optional chain_ids parameter, " +
                "returning an array of objects with protocol details and balance information across all chains."
)
async def get_all_simple_protocol_list(id: str, chain_ids: str = None):
    """
    Args:
        id : string required, user address
        chain_ids : string optional, comma-separated list of chain ids, eg: eth,bsc,xdai
    """
    url = f"{BASE_URL}/v1/user/all_simple_protocol_list?id={id}"
    if chain_ids:
        url += f"&chain_ids={chain_ids}"
    return await make_nws_request(url)

@mcp.tool(
    description="Get a list of tokens authorized by a user on a specific blockchain using a GET request to /v1/user/token_auth_list with required id and chain_id parameters, " +
                "returning an array of token authorization objects with details like token ID, spender address, and authorization amount."
)
async def get_user_token_authorized_list(id: str, chain_id: str):
    """
    Args:
        id : string required, user address
        chain_id : string required, chain id, eg: eth, bsc, xdai
    """
    return await make_nws_request(f"{BASE_URL}/v1/user/token_auth_list?id={id}&chain_id={chain_id}")



@mcp.tool(
    description="Get a list of NFTs authorized by a user on a specific blockchain using a GET request to /v1/user/nft_auth_list with required id and chain_id parameters, " +
                "returning an array of NFT authorization objects with details like NFT ID, collection info, and authorization status."
)
async def get_user_nft_authorized_list(id: str, chain_id: str):
    """
    Args:
        id : string required, user address
        chain_id : string required, chain id, eg: eth, bsc, xdai
    """
    return await make_nws_request(f"{BASE_URL}/v1/user/nft_auth_list?id={id}&chain_id={chain_id}")



# TAG:wallet

@mcp.tool(
    description="Get gas prices for a specific blockchain using a GET request to /v1/wallet/gas_market with a required chain_id parameter, " +
                "returning an array of objects with gas price levels (slow, normal, fast) and their corresponding prices."
)
async def get_wallet_gas_market(chain_id: str):
    """
    Args:
        chain_id : string required, chain id, eg: eth, bsc, xdai
    """
    return await make_nws_request(f"{BASE_URL}/v1/wallet/gas_market?chain_id={chain_id}")


@mcp.tool(
    description="Explain a transaction using a POST request to /v1/wallet/explain_tx with a required tx parameter, " +
                "returning details about the ABI function call and actions performed by the transaction."
)
async def explain_tx(tx: dict):
    """
    Args:
        tx : dict required, transaction object
    """
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "AccessKey": ACCESS_KEY
    }
    
    data = {"tx": tx}
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(f"{BASE_URL}/v1/wallet/explain_tx", json=data, headers=headers, timeout=30.0)
            response.raise_for_status()
            return response.json()
        except Exception:
            return None


if __name__ == "__main__":
    # Initialize and run the server
    mcp.run(transport='sse')


