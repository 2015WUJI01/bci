## ADDED Requirements

### Requirement: Bulk candle upsert

The system SHALL provide `BulkUpsertCandles` that accepts a batch of candle tick inputs and performs upsert for all of them in a single database round-trip, returning the resulting candles grouped by stock ID and period.

#### Scenario: All candles are new (first tick for all stocks)
- **WHEN** `BulkUpsertCandles` is called with N candle tick inputs where none of the (stock_id, period, open_time) combinations exist yet
- **THEN** the system inserts N new candle rows with open/high/low/close set to the input price
- **AND** volume is set to 0 for each new candle
- **AND** returns a map containing all N candles grouped by stock ID and period

#### Scenario: Candle already exists — update high
- **WHEN** `BulkUpsertCandles` receives a candle tick input where the candle already exists and the input price is higher than the existing high
- **THEN** the system updates the candle's high to the input price
- **AND** updates close to the input price

#### Scenario: Candle already exists — update low
- **WHEN** `BulkUpsertCandles` receives a candle tick input where the candle already exists and the input price is lower than the existing low (and existing low is not 0)
- **THEN** the system updates the candle's low to the input price
- **AND** updates close to the input price

#### Scenario: Candle already exists — low is 0
- **WHEN** `BulkUpsertCandles` receives a candle tick input where the candle already exists and its low is 0
- **THEN** the system sets the candle's low to the input price regardless of value
- **AND** updates close to the input price

#### Scenario: Empty input
- **WHEN** `BulkUpsertCandles` is called with an empty slice
- **THEN** the system returns an empty map without executing any database queries

### Requirement: Aggregate candles in batch

The `TradingTicker.aggregateAllCandles` method SHALL use `BulkUpsertCandles` instead of iterating over stocks and calling `UpsertCandle` individually.

#### Scenario: Tick with active stocks
- **WHEN** `aggregateAllCandles` is called with a list of stocks where some have CurrentPrice > 0
- **THEN** the system collects all (stockID, period, openTime, price) tuples for the 3 periods (15t/60t/150t) for each valid stock
- **AND** calls `BulkUpsertCandles` once with the full batch
- **AND** returns a `map[uint]map[string]domain.Candle` with the same structure as before

#### Scenario: Stock with zero or negative price skipped
- **WHEN** a stock in the input list has CurrentPrice <= 0
- **THEN** that stock is excluded from the bulk upsert batch and from the return map
