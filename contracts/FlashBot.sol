// SPDX-License-Identifier: MIT
pragma solidity 0.8.0;
pragma abicoder v2;


import "hardhat/console.sol";

// Uniswap imports

import '@uniswap/v3-core/contracts/interfaces/callback/IUniswapV3FlashCallback.sol';
import '@uniswap/v3-core/contracts/libraries/LowGasSafeMath.sol';

import '@uniswap/v3-periphery/contracts/base/PeripheryPayments.sol';
import '@uniswap/v3-periphery/contracts/base/PeripheryImmutableState.sol';
import '@uniswap/v3-periphery/contracts/libraries/PoolAddress.sol';
import '@uniswap/v3-periphery/contracts/libraries/CallbackValidation.sol';
import '@uniswap/v3-periphery/contracts/libraries/TransferHelper.sol';
import '@uniswap/v3-periphery/contracts/interfaces/ISwapRouter.sol';


contract uniSwapTransactBot is IUniswapV3FlashCallback, PeripheryImmutableState, PeripheryPayments {

    using LowGasSafeMath for uint256;
    using LowGasSafeMath for int256;
    address public routerAddress = 0x1b02dA8Cb0d097eB8D57A175b88c7D8b47997506; // sushiswap router address
    IUniswapRouter public router = IUniswapRouter(routerAddress);

    ISwapRouter public immutable swapRouter;

    FlashParams p;

    constructor(
        ISwapRouter _swapRouter,
        address _factory,
        address _WETH9
    ) PeripheryImmutableState(_factory, _WETH9) {
        swapRouter = _swapRouter;
    }

    function swapTokens(uint amountIn, uint amountOutMin, uint deadline) external {
        address[] memory path = new address[](2);
        path[0] = p.stoken0;
        path[1] = p.stoken1;

        // Approve the router to spend token A
        IERC20(p.stoken0).approve(routerAddress, amountIn);

        // Swap token A for token B
        swapRouter.swapExactTokensForTokens(
            amountIn,
            amountOutMin,
            path,
            msg.sender,
            deadline
        );
    }

    function uniswapV3FlashCallback(
        uint256 fee0,
        uint256 fee1,
        bytes calldata data
    ) {
        FlashCallbackData memory decoded = abi.decode(data, (FlashCallbackData));
        CallbackValidation.verifyCallback(factory, decoded.poolKey);

        address token0 = decoded.poolKey.token0;
        address token1 = decoded.poolKey.token1;

        uint amount_swap = decoded.amount0;

        TransferHelper.safeApprove(token0, address(swapRouter), decoded.amount0);
        TransferHelper.safeApprove(token1, address(swapRouter), decoded.amount1);


        // Do the first transaction
        uint256 amountOut0 =
            swapRouter.exactInputSingle(
                ISwapRouter.ExactInputSingleParams({
                    tokenIn: token1,
                    tokenOut: token0,
                    fee: decoded.poolFee2,
                    recipient: address(this),
                    deadline: block.timestamp,
                    amountIn: decoded.amount1,
                    amountOutMinimum: amount0Min,
                    sqrtPriceLimitX96: 0
                })
            );

        address[] memory path = new address[](2);
        path[0] = p.stoken0;
        path[1] = p.stoken1;
        
        router.swapExactTokensforTokens(
            amountOut0,
            decoded.amount1,
            path,
            msg.sender,
            block.timestamp
        );

        // uint256 amountOut1 =
        //     swapRouter.exactInputSingle(
        //         ISwapRouter.ExactInputSingleParams({
        //             tokenIn: token0,
        //             tokenOut: token1,
        //             fee: decoded.poolFee3,
        //             recipient: address(this),
        //             deadline: block.timestamp,
        //             amountIn: decoded.amount0,
        //             amountOutMinimum: amount1Min,
        //             sqrtPriceLimitX96: 0
        //         })
        //     );

        uint256 amount0Owed = LowGasSafeMath.add(decoded.amount0, fee0);
        uint256 amount1Owed = LowGasSafeMath.add(decoded.amount1, fee1);

        TransferHelper.safeApprove(token0, address(this), amount0Owed);
        TransferHelper.safeApprove(token1, address(this), amount1Owed);

        if (amount0Owed > 0) pay(token0, address(this), msg.sender, amount0Owed);
        if (amount1Owed > 0) pay(token1, address(this), msg.sender, amount1Owed);

        if (amountOut0 > amount0Owed) {
            uint256 profit0 = LowGasSafeMath.sub(amountOut0, amount0Owed);

            TransferHelper.safeApprove(token0, address(this), profit0);
            pay(token0, address(this), decoded.payer, profit0);
        }
    }

    struct FlashParams {
        address token0;
        address token1;
        address stoken0;
        address stoken1;
        uint24 fee1;
        uint256 amount0;
        uint256 amount1;
        uint24 fee2;
        uint24 fee3;
    }

    struct FlashCallbackData {
        uint256 amount0;
        uint256 amount1;
        address payer;
        PoolAddress.PoolKey poolKey;
    }

    function initFlash(FlashParams memory params) external {
        // (string memory e1, string memory id1, string memory id2) = splitStringInfo(first);
        // (string memory e2, string memory id3, string memory id4) = splitStringInfo(second);

        // console.log(e1, "\n");
        // console.log(id1, " ", id2);
        // console.log(e2, "\n");
        // console.log(id3, " ", id4);

        p = params;

        PoolAddress.PoolKey memory poolKey =
            PoolAddress.PoolKey({token0: params.token0, token1: params.token1, fee: params.fee1});

        IUniswapV3Pool pool = IUniswapV3Pool(PoolAddress.computeAddress(factory, poolKey));

        pool.flash(
            address(this),
            params.amount0,
            params.amount1,
            abi.encode(
                FlashCallbackData({
                    amount0: params.amount0,
                    amount1: params.amount1,
                    payer: msg.sender,
                    poolKey: poolKey,
                    poolFee2: params.fee2,
                    poolFee3: params.fee3
                })
            )
        );

    }
}


