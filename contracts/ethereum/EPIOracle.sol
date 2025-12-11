// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@chainlink/contracts/src/v0.8/interfaces/AggregatorV3Interface.sol";

/**
 * @title EPIOracle
 * @notice Mock EPI oracle for testing - implements Chainlink AggregatorV3Interface
 * @dev In production, replace with actual Chainlink oracle or custom oracle solution
 */
contract EPIOracle is AggregatorV3Interface {
    uint8 public constant override decimals = 6;  // EPI scaled to 1e6
    string public constant override description = "EPI / USD";
    uint256 public constant override version = 1;

    struct RoundData {
        int256 answer;
        uint256 startedAt;
        uint256 updatedAt;
        uint80 answeredInRound;
    }

    mapping(uint80 => RoundData) private rounds;
    uint80 private latestRound;

    event AnswerUpdated(int256 indexed current, uint256 indexed roundId, uint256 updatedAt);

    constructor() {
        // Initialize with a default EPI value of 0.75 (750000 with 6 decimals)
        updateAnswer(750000);
    }

    /**
     * @notice Update the EPI value (only for testing)
     * @param _answer New EPI value (scaled by 1e6)
     */
    function updateAnswer(int256 _answer) public {
        latestRound++;
        rounds[latestRound] = RoundData({
            answer: _answer,
            startedAt: block.timestamp,
            updatedAt: block.timestamp,
            answeredInRound: latestRound
        });
        emit AnswerUpdated(_answer, latestRound, block.timestamp);
    }

    function getRoundData(uint80 _roundId)
        external
        view
        override
        returns (
            uint80 roundId,
            int256 answer,
            uint256 startedAt,
            uint256 updatedAt,
            uint80 answeredInRound
        )
    {
        RoundData memory round = rounds[_roundId];
        return (_roundId, round.answer, round.startedAt, round.updatedAt, round.answeredInRound);
    }

    function latestRoundData()
        external
        view
        override
        returns (
            uint80 roundId,
            int256 answer,
            uint256 startedAt,
            uint256 updatedAt,
            uint80 answeredInRound
        )
    {
        RoundData memory round = rounds[latestRound];
        return (latestRound, round.answer, round.startedAt, round.updatedAt, round.answeredInRound);
    }
}
