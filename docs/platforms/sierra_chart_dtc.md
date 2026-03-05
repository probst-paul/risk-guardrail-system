# Sierra Chart DTC Mapping

This document captures Sierra Chart DTC account-level data mapping into the project's canonical account snapshot model.

## Scope

Current scope is account-level risk inputs. Position-level and fill-level streams are tracked separately and are not part of this first canonical account snapshot commit.

## Required now

Map these fields in the initial connector snapshot pipeline:

- `TradeAccount` -> `source_account_id`
- snapshot timestamp (`DateTime` when available) -> `event_ts`
- `CashBalance` -> `current_balance`
- `DailyProfitLoss` -> `daily_pnl`
- `AccountCurrency` -> `account_currency`
- `TradingIsDisabled` -> `trading_is_disabled`

Optional in this same slice:

- `DailyNetLossLimit` -> `daily_net_loss_limit`
- `starting_balance` when available natively from source-side account data

## Include later (account-level enrichments)

- `BalanceAvailableForNewPositions`
- `SecuritiesValue`
- `MarginRequirement`
- `OpenPositionsProfitLoss`
- `IsUnderRequiredMargin`
- `Description`
- `IntroducingBroker`
- `TransactionId`
- `InfoText`

## Separate stream models (later)

These should be modeled in dedicated streams, not mixed into the base account snapshot contract:

- `PositionUpdate` (`Quantity`, `AveragePrice`, `OpenProfitLoss`, `MarginRequirement`, symbol-level state)
- `OrderUpdate` (`FilledQuantity`, `LastFillPrice`, `LastFillDateTime`, `AverageFillPrice`)
- `HistoricalOrderFillResponse` (`Price`, `Quantity`, `DateTime`, `TradeAccount`, `UniqueExecutionID`)

## Derivation policy

Derivations are connector-level decisions and should remain explicit and testable.

Examples:

- `daily_trade_count` should be derived later from executions/fills, not from base account snapshots.
- `starting_balance` may be derived later when rules are finalized and connector evidence is reliable.

## Notes

- Keep canonical account snapshot schema connector-agnostic.
- Keep Sierra-specific field names and transformation rules inside connector mapping code and docs.
