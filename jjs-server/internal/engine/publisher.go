package engine

var OnTradeExecuted func(buyerID, sellerID string)
var OnTradeRecorded func(symbol string, price, qty int64)
