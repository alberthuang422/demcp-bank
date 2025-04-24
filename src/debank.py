from typing import Any
import httpx
from mcp.server.fastmcp import FastMCP

# Initialize FastMCP server
mcp = FastMCP("debank",host="0.0.0.0",port=8080)

ACCESS_KEY = "c999205e9185cef6e77e536bdd850db0831dffc9"
BASE_URL = "https://pro-openapi.debank.com"
# USER_AGENT = "DEMCP-DEBANK/1.0"

# Pagination utility function
def paginate_results(results, page=1, page_size=5):
    """Pagination utility function to extract a specific page of data from results
    
    Args:
        results: Original result list
        page: Page number, starting from 1
        page_size: Number of items per page, default is 5
        
    Returns:
        Paginated results list and pagination information
    """
    if results is None or not isinstance(results, list):
        return results
    
    start_idx = (page - 1) * page_size
    end_idx = start_idx + page_size
    total_items = len(results)
    total_pages = (total_items + page_size - 1) // page_size
    
    paginated_results = results[start_idx:end_idx]
    
    pagination_info = {
        "page": page,
        "page_size": page_size,
        "total_items": total_items,
        "total_pages": total_pages
    }
    
    return {
        "data": paginated_results,
        "pagination": pagination_info
    }

async def make_nws_request(url: str) -> dict[str, Any] | None:
    """Make a network request with error handling"""
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

async def make_post_request(url: str, data: dict) -> dict[str, Any] | None:
    """Make a POST request with error handling"""
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "AccessKey": ACCESS_KEY
    }
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(url, json=data, headers=headers, timeout=30.0)
            response.raise_for_status()
            return response.json()
        except Exception:
            return None

# TAG: Chain API
@mcp.tool(
    description="Get information about blockchains via GET requests to /v1/chain or /v1/chain/list. "+
                "Can retrieve details about a specific chain or list all supported chains."
)
async def get_chain_info(id: str = None, page: int = 1, page_size: int = 5):
    """Get blockchain information
    
    Args:
        id: Optional chain identifier (e.g. eth, bsc, xdai). If provided, returns details for that specific chain.
           If omitted, returns the list of all supported chains.
        page: Page number, starting from 1 (only used when retrieving chain list)
        page_size: Number of records per page, default is 5 (only used when retrieving chain list)
    
    Returns:
        When id is provided: An object with details about the specific chain, including ID, community ID, name, 
        logo URL, native token ID, wrapped token ID, and pre-execution support status.
        
        When id is omitted: A paginated object with an array of chains and pagination information.
    """
    if id:
        return await make_nws_request(f"{BASE_URL}/v1/chain?id={id}")
    else:
        results = await make_nws_request(f"{BASE_URL}/v1/chain/list")
        return paginate_results(results, page, page_size)

# TAG: Protocol API
@mcp.tool(
    description="Get information about DeFi protocols via GET requests to various protocol endpoints. "+
                "Can retrieve details about a specific protocol, list protocols on a chain, or fetch top holders."
)
async def get_protocol_info(id: str = None, chain_id: str = None, get_top_holders: bool = False, 
                           start: int = None, limit: int = 10, page: int = 1, page_size: int = 5):
    """Get protocol information
    
    Args:
        id: Protocol identifier (e.g. curve, uniswap). Required when getting specific protocol info or top holders.
        chain_id: Chain identifier (e.g. eth, bsc). Required when listing protocols on a chain.
        get_top_holders: Set to True to fetch the top holders of a protocol. Requires id to be set.
        start: Integer offset for pagination when getting top holders, default is 0, maximum is 1000
        limit: Number of results to return. For protocol list: number of top protocols by TVL (default: 10).
              For top holders: number of holders to return (default: 10, maximum: 100).
        page: Page number, starting from 1 (only used when retrieving list data)
        page_size: Number of records per page, default is 5 (only used when retrieving list data)
    
    Returns:
        When id is provided and get_top_holders is False: An object with details about the specific protocol.
        When chain_id is provided and id is None: A paginated object with protocols on the specified chain.
        When id is provided and get_top_holders is True: A paginated object with top holders.
    
    Note:
        The protocol list and top holders endpoints can return large amounts of data.
        Pagination is applied to limit the results.
    """
    if id and get_top_holders:
        # Get top holders of a protocol
        url = f"{BASE_URL}/v1/protocol/top_holders?id={id}"
        if start is not None:
            url += f"&start={start}"
        if limit is not None:
            url += f"&limit={limit}"
        results = await make_nws_request(url)
        return paginate_results(results, page, page_size)
    elif id:
        # Get specific protocol info
        return await make_nws_request(f"{BASE_URL}/v1/protocol?id={id}")
    elif chain_id:
        # Get protocols on a chain
        protocols = await make_nws_request(f"{BASE_URL}/v1/protocol/list?chain_id={chain_id}")
        if protocols:
            # Sort protocols by TVL in descending order
            sorted_protocols = sorted(protocols, key=lambda x: x.get('tvl', 0), reverse=True)
            return paginate_results(sorted_protocols, page, page_size)
        return None
    else:
        return {"error": "Either id or chain_id must be provided"}

# TAG: Token API
@mcp.tool(
    description="Get information about tokens via GET requests to various token endpoints. "+
                "Can retrieve token details, top holders, or historical prices."
)
async def get_token_info(chain_id: str, id: str, action: str = "details", date_at: str = None, 
                        start: int = 0, limit: int = 100, page: int = 1, page_size: int = 5):
    """Get token information
    
    Args:
        chain_id: Chain identifier, required parameter (e.g. eth, bsc, xdai)
        id: Token identifier - either a contract address or a native token id (e.g. eth, matic, bsc)
        action: Type of information to retrieve:
               - "details" (default): Get basic token details
               - "holders": Get top token holders
               - "history": Get historical price (requires date_at parameter)
        date_at: UTC timezone date in YYYY-MM-DD format (e.g. 2023-05-18), required for historical price
        start: Integer offset for pagination when getting top holders, default is 0, maximum is 10000
        limit: Number of holders to return, default is 100, maximum is 100
        page: Page number, starting from 1 (only used when retrieving holder list)
        page_size: Number of records per page, default is 5 (only used when retrieving holder list)
    
    Returns:
        For "details": An object with token information including name, symbol, decimals, price, etc.
        For "holders": A paginated object with top token holders and pagination information
        For "history": An object with the historical price at the specified date
    
    Note:
        The top holders endpoint returns large amounts of data.
        Pagination is applied to limit the results.
    """
    if action == "details":
        return await make_nws_request(f"{BASE_URL}/v1/token?chain_id={chain_id}&id={id}")
    elif action == "holders":
        url = f"{BASE_URL}/v1/token/top_holders?chain_id={chain_id}&id={id}&start={start}&limit={limit}"
        results = await make_nws_request(url)
        return paginate_results(results, page, page_size)
    elif action == "history":
        if not date_at:
            return {"error": "date_at parameter is required for historical price"}
        return await make_nws_request(f"{BASE_URL}/v1/token/history_price?chain_id={chain_id}&id={id}&date_at={date_at}")
    else:
        return {"error": "Invalid action parameter. Use 'details', 'holders', or 'history'."}

# TAG: Pool API
@mcp.tool(
    description="Get detailed information about a specific liquidity pool via a GET request to /v1/pool. "+
                "Returns detailed statistics about the pool including its deposits, user counts, and associated protocol."
)
async def get_pool_info(id: str, chain_id: str):
    """Get detailed information about a specific liquidity pool
    
    Args:
        id: Pool identifier, required parameter (e.g. 0x00000000219ab540356cbb839cbe05303d7705fa)
        chain_id: Chain identifier, required parameter (e.g. eth, bsc, xdai)
    
    Returns:
        An object with the following fields:
        - pool_id: The pool's identifier
        - chain: The chain's ID
        - protocol_id: Protocol ID associated with the pool
        - contract_ids: List of contract IDs associated with the pool
        - name: The pool's name
        - stats: Object containing:
            - deposit_usd_value: Total USD value of assets stored in this pool
            - deposit_user_count: Total number of users with deposits in this pool
            - deposit_valuable_user_count: Number of users with deposits over $100 in this pool
    """
    return await make_nws_request(f"{BASE_URL}/v1/pool?id={id}&chain_id={chain_id}")

# TAG: User API - Assets
@mcp.tool(
    description="Get information about a user's assets across different blockchains. "+
                "Can retrieve basic balance, token lists, NFTs, and more with optional chain filtering."
)
async def get_user_assets(id: str, asset_type: str = "balance", chain_id: str = None, 
                         token_id: str = None, chain_ids: str = None, page: int = 1, page_size: int = 5):
    """Get information about a user's blockchain assets
    
    Args:
        id: User wallet address, required parameter
        asset_type: Type of asset information to retrieve:
                - "balance": Get total USD balance (default)
                - "chains": List blockchains used by the user
                - "tokens": List token balances
                - "token": Get balance of a specific token (requires chain_id and token_id)
                - "nfts": List NFT holdings
        chain_id: Chain identifier for single-chain queries (e.g. eth, bsc, xdai)
        token_id: Token identifier for specific token balance query
        chain_ids: Optional comma-separated list of chain IDs to filter multi-chain results (e.g. "eth,bsc,xdai")
        page: Page number, starting from 1 (only used when retrieving list data)
        page_size: Number of records per page, default is 5 (only used when retrieving list data)
    
    Returns:
        Response varies based on asset_type:
        - "balance": Object with total_usd_value and chain breakdown when no chain_id provided,
                    or single chain balance when chain_id provided
        - "chains": Paginated array of blockchain objects used by the user
        - "tokens": Paginated array of token objects owned by the user
        - "token": Object with balance details for a specific token
        - "nfts": Paginated array of NFT objects owned by the user
    
    Note:
        Token and NFT list endpoints return large amounts of data.
        Pagination is applied to limit the results.
    """
    if asset_type == "balance":
        if chain_id:
            return await make_nws_request(f"{BASE_URL}/v1/user/chain_balance?id={id}&chain_id={chain_id}")
        else:
            url = f"{BASE_URL}/v1/user/total_balance?id={id}"
            if chain_ids:
                url += f"&chain_ids={chain_ids}"
            return await make_nws_request(url)
    elif asset_type == "chains":
        results = await make_nws_request(f"{BASE_URL}/v1/user/used_chain_list?id={id}")
        return paginate_results(results, page, page_size)
    elif asset_type == "tokens":
        if chain_id:
            results = await make_nws_request(f"{BASE_URL}/v1/user/token_list?id={id}&chain_id={chain_id}")
        else:
            url = f"{BASE_URL}/v1/user/all_token_list?id={id}"
            if chain_ids:
                url += f"&chain_ids={chain_ids}"
            results = await make_nws_request(url)
        return paginate_results(results, page, page_size)
    elif asset_type == "token":
        if not chain_id or not token_id:
            return {"error": "chain_id and token_id are required for token balance query"}
        return await make_nws_request(f"{BASE_URL}/v1/user/token_balance?id={id}&chain_id={chain_id}&token_id={token_id}")
    elif asset_type == "nfts":
        if chain_id:
            results = await make_nws_request(f"{BASE_URL}/v1/user/nft_list?id={id}&chain_id={chain_id}")
        else:
            url = f"{BASE_URL}/v1/user/all_nft_list?id={id}"
            if chain_ids:
                url += f"&chain_ids={chain_ids}"
            results = await make_nws_request(url)
        return paginate_results(results, page, page_size)
    else:
        return {"error": "Invalid asset_type parameter"}

# TAG: User API - Protocols and History
@mcp.tool(
    description="Get information about a user's protocol positions, transaction history, and balance charts. "+
                "Supports filtering by chain and protocol."
)
async def get_user_activities(id: str, activity_type: str, chain_id: str = None, protocol_id: str = None, 
                             chain_ids: str = None, page_count: int = None, start_time: int = None, 
                             is_simple: bool = True, page: int = 1, page_size: int = 5):
    """Get information about a user's protocol positions, history, and balance changes
    
    Args:
        id: User wallet address, required parameter
        activity_type: Type of activity information to retrieve:
                      - "protocols": Get user's protocol positions
                      - "history": Get transaction history
                      - "chart": Get 24-hour balance chart data
        chain_id: Chain identifier for single-chain queries (e.g. eth, bsc, xdai)
        protocol_id: Protocol identifier for specific protocol query (required when querying a specific protocol)
        chain_ids: Optional comma-separated list of chain IDs for multi-chain queries (e.g. "eth,bsc,xdai")
        page_count: Optional number of pages to return for history queries
        start_time: Optional Unix timestamp to start from for history queries
        is_simple: For protocol queries, whether to use simple (True) or complex (False) protocol list
        page: Page number, starting from 1 (only used when retrieving list data)
        page_size: Number of records per page, default is 5 (only used when retrieving list data)
    
    Returns:
        Response varies based on activity_type:
        - "protocols": Paginated protocol positions data
        - "history": Paginated transaction history data
        - "chart": Paginated 24-hour balance chart data as timestamp-value pairs
    
    Note:
        History and complex protocol list endpoints return large amounts of data.
        Pagination is applied to limit the results.
    """
    if activity_type == "protocols":
        if protocol_id:
            # Get specific protocol info
            return await make_nws_request(f"{BASE_URL}/v1/user/protocol?id={id}&protocol_id={protocol_id}")
        elif chain_id:
            # Get protocol list for a specific chain
            if is_simple:
                results = await make_nws_request(f"{BASE_URL}/v1/user/simple_protocol_list?id={id}&chain_id={chain_id}")
            else:
                results = await make_nws_request(f"{BASE_URL}/v1/user/complex_protocol_list?id={id}&chain_id={chain_id}")
            return paginate_results(results, page, page_size)
        else:
            # Get protocol list for all chains
            url_base = f"{BASE_URL}/v1/user/all_"
            url_base += "simple_protocol_list" if is_simple else "complex_protocol_list"
            url = f"{url_base}?id={id}"
            if chain_ids:
                url += f"&chain_ids={chain_ids}"
            results = await make_nws_request(url)
            return paginate_results(results, page, page_size)
    elif activity_type == "history":
        if chain_id:
            # Get history for a specific chain
            url = f"{BASE_URL}/v1/user/history_list?id={id}&chain_id={chain_id}"
            if page_count is not None:
                url += f"&page_count={page_count}"
            if start_time is not None:
                url += f"&start_time={start_time}"
            results = await make_nws_request(url)
            return paginate_results(results, page, page_size)
        else:
            # Get history for all chains
            url = f"{BASE_URL}/v1/user/history?id={id}"
            if chain_ids:
                url += f"&chain_ids={chain_ids}"
            if page_count is not None:
                url += f"&page_count={page_count}"
            if start_time is not None:
                url += f"&start_time={start_time}"
            results = await make_nws_request(url)
            return paginate_results(results, page, page_size)
    elif activity_type == "chart":
        if chain_id:
            # Get chart for a specific chain
            results = await make_nws_request(f"{BASE_URL}/v1/user/chain_net_curve?id={id}&chain_id={chain_id}")
            return paginate_results(results, page, page_size)
        else:
            # Get chart for all chains
            url = f"{BASE_URL}/v1/user/total_net_curve?id={id}"
            if chain_ids:
                url += f"&chain_ids={chain_ids}"
            results = await make_nws_request(url)
            return paginate_results(results, page, page_size)
    else:
        return {"error": "Invalid activity_type parameter"}

# TAG: User API - Authorizations
@mcp.tool(
    description="Get information about a user's token and NFT authorizations on a specific blockchain."
)
async def get_user_authorizations(id: str, chain_id: str, auth_type: str = "token", page: int = 1, page_size: int = 5):
    """Get information about a user's token and NFT authorizations
    
    Args:
        id: User wallet address, required parameter
        chain_id: Chain identifier, required parameter (e.g. eth, bsc, xdai)
        auth_type: Type of authorization to retrieve:
                  - "token": Get token authorizations (default)
                  - "nft": Get NFT authorizations
        page: Page number, starting from 1
        page_size: Number of records per page, default is 5
    
    Returns:
        A paginated array of authorization objects:
        - For tokens: Details about token approvals including spender addresses and amounts
        - For NFTs: Details about NFT approvals including contracts and approval status
    """
    if auth_type == "token":
        results = await make_nws_request(f"{BASE_URL}/v1/user/token_auth_list?id={id}&chain_id={chain_id}")
        return paginate_results(results, page, page_size)
    elif auth_type == "nft":
        results = await make_nws_request(f"{BASE_URL}/v1/user/nft_auth_list?id={id}&chain_id={chain_id}")
        return paginate_results(results, page, page_size)
    else:
        return {"error": "Invalid auth_type parameter. Use 'token' or 'nft'."}

# TAG: Collection API
@mcp.tool(
    description="Get a list of NFTs in a specific collection using a GET request to /v1/collection/nft_list. "+
                "Returns an array of NFT objects with details like name, description, content, and attributes."
)
async def get_collection_nft_list(id: str, chain_id: str, start: int = 0, limit: int = 20, page: int = 1, page_size: int = 5):
    """Get a list of NFTs in a specific collection
    
    Args:
        id: NFT contract address, required parameter
        chain_id: Chain identifier, required parameter (e.g. eth, bsc, xdai)
        start: Integer offset for pagination, default is 0, maximum is 100000
        limit: Number of NFTs to return, default is 20, maximum is 100
        page: Page number, starting from 1
        page_size: Number of records per page, default is 5
    
    Returns:
        A paginated array of NFT objects, each containing:
        - id: Unique NFT identifier
        - contract_id: The address of the token contract
        - inner_id: The token ID within the contract
        - name: The NFT's name
        - description: The NFT's description
        - content_type: Type of content (e.g. image_url, video_url, audio_url)
        - content: The NFT's content URL
        - detail_url: URL to the NFT's detail page
        - thumbnail_url: URL to the NFT's thumbnail image
        - contract_name: Name of the NFT contract
        - is_erc1155: Whether the NFT uses ERC-1155 standard
        - is_erc721: Whether the NFT uses ERC-721 standard
        - attributes: Array of trait objects with trait_type and value fields
    """
    url = f"{BASE_URL}/v1/collection/nft_list?id={id}&chain_id={chain_id}&start={start}&limit={limit}"
    results = await make_nws_request(url)
    return paginate_results(results, page, page_size)

# TAG: Wallet API
@mcp.tool(
    description="Access wallet-related functionality: get gas prices, analyze transactions, or simulate transactions."
)
async def wallet_tools(action: str, chain_id: str = None, tx: dict = None, pending_tx_list: list = None, page: int = 1, page_size: int = 5):
    """Access various wallet-related tools
    
    Args:
        action: Type of wallet action to perform:
               - "gas": Get current gas prices for a blockchain
               - "explain_tx": Analyze and explain a transaction
               - "simulate_tx": Simulate a transaction execution without submitting it
        chain_id: Chain identifier, required for gas price queries (e.g. eth, bsc, xdai)
        tx: Transaction object, required for explain_tx and simulate_tx
        pending_tx_list: Optional list of transactions to execute before the main transaction (for simulate_tx)
        page: Page number, starting from 1 (only used when retrieving gas price list)
        page_size: Number of records per page, default is 5 (only used when retrieving gas price list)
    
    Returns:
        For "gas": Paginated array of gas price levels (slow, normal, fast) and their values
        For "explain_tx": Detailed analysis of transaction including ABI calls and actions
        For "simulate_tx": Simulation results including balance changes and gas usage
    """
    if action == "gas":
        if not chain_id:
            return {"error": "chain_id parameter is required for gas price query"}
        results = await make_nws_request(f"{BASE_URL}/v1/wallet/gas_market?chain_id={chain_id}")
        return paginate_results(results, page, page_size)
    elif action == "explain_tx":
        if not tx:
            return {"error": "tx parameter is required for transaction explanation"}
        data = {"tx": tx}
        return await make_post_request(f"{BASE_URL}/v1/wallet/explain_tx", data)
    elif action == "simulate_tx":
        if not tx:
            return {"error": "tx parameter is required for transaction simulation"}
        data = {"tx": tx}
        if pending_tx_list:
            data["pending_tx_list"] = pending_tx_list
        return await make_post_request(f"{BASE_URL}/v1/wallet/pre_exec_tx", data)
    else:
        return {"error": "Invalid action parameter. Use 'gas', 'explain_tx', or 'simulate_tx'."}

# LLM Usage Guidance:
# 1. Prefer specific resource endpoints over list interfaces to reduce context length
#    Example: Use get_token_info with action="details" instead of listing tokens
#            Use get_user_activities with protocol_id parameter instead of listing all protocols
# 2. For list APIs, always use pagination parameters (page, page_size) to restrict data volume
# 3. High data volume APIs (now paginated by default with a max of 5 items per page):
#    - get_protocol_info with chain_id parameter (protocol listings)
#    - get_protocol_info with get_top_holders=True (holder lists)
#    - get_token_info with action="holders" (token holder lists)
#    - get_user_assets with asset_type="tokens" or "nfts" (user holdings)
#    - get_user_activities with activity_type="history" (transaction history)
#    - get_user_activities with activity_type="protocols" and is_simple=False (complex protocol details)
#    - get_collection_nft_list (NFT collection items)
# 4. When needing specific information, consider:
#    - Can you query a single resource by ID instead of listing all?
#    - Can you add filter parameters to reduce returned data?
#    - Do you need the entire list or just a few examples?

if __name__ == "__main__":
    # Initialize and run the server
    mcp.run(transport='sse')


