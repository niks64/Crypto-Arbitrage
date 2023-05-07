// SPDX-License-Identifier: MIT
pragma solidity >=0.7.0 <0.9.0;

import "hardhat/console.sol";

// Uniswap imports
import "@uniswap/v3-periphery/contracts/base/PeripheryPayments.sol";
import "@uniswap/v3-periphery/contracts/base/PeripheryImmutableState.sol";
import "@uniswap/v3-periphery/contracts/libraries/PoolAddress.sol";
import "@uniswap/v3-periphery/contracts/libraries/CallbackValidation.sol";
import "@uniswap/v3-periphery/contracts/libraries/TransferHelper.sol";
import "@uniswap/v3-periphery/contracts/interfaces/ISwapRouter.sol";

import "@openzeppelin/contracts/token/ERC20/IERC20.sol";





struct FlashParams {
    address token0;
    address token1;
    uint24 fee1;
    uint256 amount0;
    uint256 amount1;
    string sym0;
    string sym1;
}

struct FlashCallbackData {
    uint256 amount0;
    uint256 amount1;
    address payer;
    PoolAddress.PoolKey poolKey;
}

// interface IFlashBot {
//     function flashArbitrage(string memory first, string memory second, FlashParams memory params) external;
// }

contract FlashBot {

    
    function splitStringInfo(string memory input) public pure returns (string memory, string memory, string memory) {
        bytes memory b = bytes(input);
        string memory exchange = "";
        string memory id1 = "";
        string memory id2 = "";

        uint temp = 0;
        for (uint i = 0; i < b.length; i++) {
            if (b[i] == 0x2d) {
                temp = i + 1;
                break;
            }
            exchange = string(abi.encodePacked(exchange, b[i]));
        }

        for (uint i = temp; i < b.length; i++) {
            if (b[i] == 0x2d) {
                temp = i + 1;
                break;
            }
            id1 = string(abi.encodePacked(id1, b[i]));
        }

        for (uint i = temp; i < b.length; i++) {
            id2 = string(abi.encodePacked(id2, b[i]));
        }

        return (exchange, id1, id2);
    }

    function compareStrings(string memory a, string memory b) public pure returns(bool) {
        if (bytes(a).length != bytes(b).length) {
            return false;
        }
        
        for (uint i = 0; i < bytes(a).length; i++) {
            if (bytes(a)[i] != bytes(b)[i]) {
                return false;
            }
        }
        
        return true;
    }

    function transfer_wrapper(address token1, address token2, uint amount_swap) private returns (uint amount_out){
        TransferHelper.safeApprove(token1, address(swaper), amount_swap);
        amount_out = swaper.swapTokenMax(token1, token2, amount_swap);
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
         
          
    }

    function flashArbitrage(FlashParams memory params) external view {
        // (string memory e1, string memory id1, string memory id2) = splitStringInfo(first);
        // (string memory e2, string memory id3, string memory id4) = splitStringInfo(second);

        // console.log(e1, "\n");
        // console.log(id1, " ", id2);
        // console.log(e2, "\n");
        // console.log(id3, " ", id4);

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
                    poolKey: poolKey
                })
            )
        );

        IERC20(params.sym0).transfer(address(this), params.amount0);
        IERC20(params.sym1).transfer(address(this), params.amount1);

    }
}


